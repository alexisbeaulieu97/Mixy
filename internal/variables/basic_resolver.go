package variables

import (
	"fmt"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// BasicResolver implements a simple variable resolution strategy.
type BasicResolver struct {
	// Add dependencies for TUI later if needed
}

// NewBasicResolver creates a new BasicResolver.
func NewBasicResolver() core.VariableResolver {
	return &BasicResolver{}
}

// Resolve merges defaults and overrides. Does not yet handle TUI.
func (r *BasicResolver) Resolve(
	configDefaults map[string]interface{},
	flagOverrides map[string]string,
) (map[string]interface{}, error) {

	finalVars := make(map[string]interface{})

	// 1. Apply defaults from config
	for key, value := range configDefaults {
		finalVars[key] = value
	}

	// 2. Apply overrides from flags (currently string->string, need conversion maybe later)
	//    For now, we assume flags directly overwrite, treating values as strings.
	//    A more robust solution would handle type conversions or use typed flags.
	for key, value := range flagOverrides {
		fmt.Printf("Overriding variable '%s' with value '%s' from flag\n", key, value) // Debugging
		finalVars[key] = value                                                         // Direct overwrite
	}

	// 3. Placeholder for TUI interaction
	//    Here you would check for missing mandatory variables (if defined in config)
	//    and launch the TUI if needed.

	fmt.Printf("Final resolved variables: %v\n", finalVars) // Debugging
	return finalVars, nil
}
