// internal/variables/basic_resolver.go
package variables

import (
	"fmt"
	"log" // Or use hclog

	"github.com/alexisbeaulieu97/Mixy/internal/core"
	"github.com/alexisbeaulieu97/Mixy/internal/tui" // Import the TUI package
)

// BasicResolver implements a simple variable resolution strategy including TUI prompt.
type BasicResolver struct{}

// NewBasicResolver creates a new BasicResolver.
func NewBasicResolver() core.VariableResolver {
	return &BasicResolver{}
}

// Resolve merges defaults, overrides, and prompts for missing mandatory variables.
func (r *BasicResolver) Resolve(
	configDefaults map[string]interface{},
	flagOverrides map[string]string,
	mandatoryKeys []string, // Receive mandatory keys
) (map[string]interface{}, error) {

	finalVars := make(map[string]interface{})

	// 1. Apply defaults from config
	for key, value := range configDefaults {
		finalVars[key] = value
	}

	// 2. Apply overrides from flags
	for key, value := range flagOverrides {
		log.Printf("Overriding variable '%s' with value '%s' from flag\n", key, value)
		finalVars[key] = value // Direct overwrite (as string)
	}

	// 3. Check for missing mandatory variables
	missingMandatoryVars := []string{}
	if len(mandatoryKeys) > 0 {
		log.Println("Checking mandatory variables...") // Debug log
		for _, key := range mandatoryKeys {
			log.Printf("  Checking: %s\n", key) // Debug log
			if _, exists := finalVars[key]; !exists {
				log.Printf("    Mandatory variable '%s' is missing.\n", key) // Debug log
				missingMandatoryVars = append(missingMandatoryVars, key)
			} else {
				log.Printf("    Mandatory variable '%s' is present: %v\n", key, finalVars[key]) // Debug log
			}
		}
	} else {
		log.Println("No mandatory variables defined in config.") // Debug log
	}

	// 4. If mandatory variables are missing, launch TUI prompt
	if len(missingMandatoryVars) > 0 {
		fmt.Printf("Mandatory variables missing: %v. Launching interactive prompt...\n", missingMandatoryVars)

		// Call the TUI runner function
		providedValues, err := tui.RunPrompt(missingMandatoryVars)
		if err != nil {
			// Handle errors, including user cancellation (tui.ErrUserCancelled)
			return nil, fmt.Errorf("failed during interactive prompt: %w", err)
		}

		// Merge the values provided by the user
		log.Printf("Merging values from TUI: %v\n", providedValues) // Debug log
		for key, value := range providedValues {
			finalVars[key] = value // Add user-provided values (as string)
		}
		fmt.Println("Interactive input collected.")
	}

	log.Printf("Final resolved variables: %v\n", finalVars) // Debug log
	return finalVars, nil
}
