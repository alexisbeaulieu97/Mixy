package config

import (
	"fmt"
	"strings"

	"github.com/alexisbeaulieu97/Mixy/internal/core" // Use the core types
	"github.com/spf13/viper"
)

// ViperLoader uses the Viper library to load configuration.
type ViperLoader struct{}

// NewViperLoader creates a new ViperLoader instance.
func NewViperLoader() core.ConfigLoader {
	return &ViperLoader{}
}

// Load reads and parses the configuration file using Viper.
func (vl *ViperLoader) Load(filePath string) (*core.Config, error) {
	v := viper.New()
	v.SetConfigFile(filePath)

	// Allow reading environment variables (optional, but good practice)
	v.SetEnvPrefix("MIXY") // e.g., MIXY_OUTPUT=/path/to/out
	v.AutomaticEnv()
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))

	if err := v.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			return nil, fmt.Errorf("config file not found: %s", filePath)
		}
		return nil, fmt.Errorf("failed to read config file '%s': %w", filePath, err)
	}

	var cfg core.Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config file '%s': %w", filePath, err)
	}

	// Basic validation (can be expanded)
	if len(cfg.Templates) == 0 {
		fmt.Println("Warning: No templates defined in the configuration.")
		// Depending on requirements, this could be an error:
		// return nil, fmt.Errorf("no templates defined in config: %s", filePath)
	}

	fmt.Printf("Loaded configuration from %s\n", filePath)       // Debugging
	fmt.Printf("Configured Templates: %d\n", len(cfg.Templates)) // Debugging
	fmt.Printf("Default Variables: %v\n", cfg.Variables)         // Debugging
	fmt.Printf("Default Output: %s\n", cfg.Output)               // Debugging

	return &cfg, nil
}
