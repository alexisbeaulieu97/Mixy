// internal/variables/basic_resolver.go
package variables

import (
	"errors" // Import errors
	"fmt"
	"log/slog"

	"github.com/alexisbeaulieu97/Mixy/internal/core" // Use specific path
	"github.com/alexisbeaulieu97/Mixy/internal/tui"
)

// BasicResolver implements variable resolution including TUI prompt.
type BasicResolver struct{}

// NewBasicResolver creates a new BasicResolver.
func NewBasicResolver() core.VariableResolver {
	return &BasicResolver{}
}

// Resolve merges defaults, overrides, and prompts for missing mandatory variables.
func (r *BasicResolver) Resolve(
	configDefaults map[string]interface{},
	flagOverrides map[string]string,
	mandatoryKeys []string,
	ctx *core.ProjectContext,
) (map[string]interface{}, error) {
	logger := ctx.Logger.With(slog.String("component", "variable_resolver"))
	finalVars := make(map[string]interface{}) // Create NEW map

	// --- Stage 1: Defaults ---
	logger.Debug("--- Resolving Stage 1: Applying Defaults ---", slog.Any("defaults_received", configDefaults))
	for key, value := range configDefaults {
		finalVars[key] = value
	}
	logger.Debug("Variables after defaults applied", slog.Any("current_vars", finalVars))

	// --- Stage 2: Flags ---
	logger.Debug("--- Resolving Stage 2: Applying Flags ---", slog.Any("flags_received", flagOverrides))
	if len(flagOverrides) > 0 {
		for key, value := range flagOverrides {
			logger.Info("Overriding variable from flag", slog.String("key", key), slog.String("value", value))
			finalVars[key] = value
		}
	}
	logger.Debug("Variables after flags applied", slog.Any("current_vars", finalVars))

	// --- Stage 3: Check Mandatory ---
	logger.Debug("--- Resolving Stage 3: Checking Mandatory ---", slog.Any("mandatory_keys", mandatoryKeys))
	missingMandatoryVars := []string{}
	if len(mandatoryKeys) > 0 {
		for _, key := range mandatoryKeys {
			val, exists := finalVars[key] // Check existence IN THE CURRENT finalVars map
			if !exists {
				logger.Warn("Mandatory variable MISSING from current map", slog.String("key", key))
				missingMandatoryVars = append(missingMandatoryVars, key)
			} else {
				// Log that it was found *at this stage*
				logger.Debug("Mandatory variable FOUND in current map", slog.String("key", key), slog.Any("value", val))
			}
		}
	} else {
		logger.Debug("No mandatory variables defined.")
	}
	logger.Debug("List of missing mandatory variables", slog.Any("missing_list", missingMandatoryVars))

	// --- Stage 4: TUI Prompt ---
	logger.Debug("--- Resolving Stage 4: Prompting TUI if needed ---")
	if len(missingMandatoryVars) > 0 {
		logger.Info("Mandatory variables missing, launching interactive prompt", slog.Any("missing", missingMandatoryVars))
		fmt.Printf("Mandatory variables missing: %v. Please provide values:\n", missingMandatoryVars) // User message

		providedValues, err := tui.RunPrompt(missingMandatoryVars)
		if err != nil {
			if errors.Is(err, tui.ErrUserCancelled) {
				logger.Warn("User cancelled interactive prompt")
				return nil, core.ErrCancelled
			}
			logger.Error("Interactive prompt failed", slog.Any("error", err))
			return nil, core.NewError(core.ErrorTypeVariable, "interactive prompt failed", err)
		}
		logger.Debug("Raw values received from TUI", slog.Any("provided_map", providedValues))

		// --- Stage 5: Merge TUI ---
		logger.Debug("--- Resolving Stage 5: Merging TUI values ---")
		for key, value := range providedValues {
			// Only add/overwrite if the TUI actually returned a value for the key
			// (RunPrompt should only return keys that were displayed and entered)
			logger.Debug("Applying TUI value", slog.String("key", key), slog.String("value", value))
			finalVars[key] = value
		}
		logger.Info("Interactive input collected and merged.")
	} else {
		logger.Debug("No TUI prompt needed.")
	}

	logger.Debug("--- Resolution Complete ---")
	logger.Info("Variable resolution complete.")
	logger.Debug("Final resolved variables being returned", slog.Any("variables", finalVars))
	return finalVars, nil
}
