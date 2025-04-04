// Package steps provides workflow step implementations for Mixy's template processing pipeline.
package steps

import (
	"errors"
	"fmt"
	"log/slog"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// ResolveVariablesStep handles the resolution of template variables by combining
// values from configuration defaults, command-line flags, and potentially
// interactive user input.
type ResolveVariablesStep struct {
	// Resolver performs the actual variable resolution
	Resolver core.VariableResolver

	// Options configures the variable resolution behavior
	Options VariableOptions
}

// VariableOptions configures how variables are resolved.
type VariableOptions struct {
	// StrictMode indicates whether undefined mandatory variables
	// should cause an error
	StrictMode bool

	// AllowInteractive indicates whether the resolver can
	// prompt for missing values
	AllowInteractive bool

	// SkipDefaults indicates whether to ignore configuration
	// default values
	SkipDefaults bool
}

// NewResolveVariablesStep creates a new step with the given resolver and options.
//
// Parameters:
//   - resolver: The VariableResolver to use for resolution
//   - options: Optional configuration for resolution behavior
//
// Returns:
//   - *ResolveVariablesStep: The configured step
//
// Panics if resolver is nil, as it's required for operation.
func NewResolveVariablesStep(resolver core.VariableResolver, options VariableOptions) *ResolveVariablesStep {
	if resolver == nil {
		panic("variable resolver is required")
	}

	return &ResolveVariablesStep{
		Resolver: resolver,
		Options:  options,
	}
}

// Name returns the step's identifier.
func (s *ResolveVariablesStep) Name() string {
	return "resolve_variables"
}

// Execute performs variable resolution by combining values from various sources
// and ensuring all required variables are set.
func (s *ResolveVariablesStep) Execute(ctx *core.ProjectContext) error {
	// Input validation
	if ctx == nil {
		return core.NewVariableError("nil context provided", nil)
	}
	if ctx.Logger == nil {
		return core.NewVariableError("nil logger in context", nil)
	}
	if ctx.Config == nil {
		return core.NewVariableError("nil configuration in context", nil)
	}

	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))

	// Log resolution attempt
	stepLogger.Info("Resolving template variables",
		slog.Int("default_count", len(ctx.Config.Variables)),
		slog.Int("flag_count", len(ctx.FlagVariables)),
		slog.Int("mandatory_count", len(ctx.Config.MandatoryVariables)))

	// Prepare configuration defaults
	configVars := ctx.Config.Variables
	if s.Options.SkipDefaults {
		stepLogger.Info("Skipping configuration defaults")
		configVars = make(map[string]interface{})
	}

	// Resolve variables
	resolvedVars, err := s.Resolver.Resolve(
		configVars,
		ctx.FlagVariables,
		ctx.Config.MandatoryVariables,
		ctx,
	)

	// Handle errors
	if err != nil {
		if errors.Is(err, core.ErrCancelled) {
			stepLogger.Warn("Variable resolution cancelled by user")
			return fmt.Errorf("variable resolution cancelled: %w", err)
		}

		// Add context to error
		if _, ok := err.(*core.MixyError); !ok {
			err = core.NewVariableError(
				"variable resolution failed",
				err,
				slog.Int("default_count", len(configVars)),
				slog.Int("flag_count", len(ctx.FlagVariables)),
				slog.Int("mandatory_count", len(ctx.Config.MandatoryVariables)))
		}

		stepLogger.Error("Failed to resolve variables",
			slog.Any("error", err))
		return err
	}

	// Validate results in strict mode
	if s.Options.StrictMode {
		if err := s.validateResolvedVariables(resolvedVars, ctx, stepLogger); err != nil {
			return err
		}
	}

	// Store results
	ctx.Variables = resolvedVars

	stepLogger.Info("Variables resolved successfully",
		slog.Int("total_variables", len(resolvedVars)))

	return nil
}

// validateResolvedVariables ensures all required variables are present and
// have non-zero values in strict mode.
func (s *ResolveVariablesStep) validateResolvedVariables(
	resolved map[string]interface{},
	ctx *core.ProjectContext,
	logger *slog.Logger,
) error {
	if len(ctx.Config.MandatoryVariables) == 0 {
		return nil
	}

	logger.Debug("Validating resolved variables in strict mode")

	for _, key := range ctx.Config.MandatoryVariables {
		value, exists := resolved[key]
		if !exists {
			return core.NewVariableError(
				fmt.Sprintf("mandatory variable '%s' is undefined", key),
				nil)
		}

		// Check for zero values based on type
		if s.isZeroValue(value) {
			return core.NewVariableError(
				fmt.Sprintf("mandatory variable '%s' has zero value", key),
				nil)
		}
	}

	return nil
}

// isZeroValue checks if the given value is the zero value for its type.
func (s *ResolveVariablesStep) isZeroValue(v interface{}) bool {
	if v == nil {
		return true
	}

	switch val := v.(type) {
	case string:
		return val == ""
	case int:
		return val == 0
	case float64:
		return val == 0
	case bool:
		return !val
	case []interface{}:
		return len(val) == 0
	case map[string]interface{}:
		return len(val) == 0
	default:
		return false
	}
}
