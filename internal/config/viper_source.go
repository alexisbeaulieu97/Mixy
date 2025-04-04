// internal/config/viper_source.go
package config

import (
	"errors"
	"log/slog" // Use slog
	"strings"

	"github.com/alexisbeaulieu97/Mixy/internal/core" // Use the core types
	"github.com/spf13/viper"
)

// ViperSource uses the Viper library to load configuration.
type ViperSource struct{}

// NewViperSource creates a new ViperSource instance.
func NewViperSource() core.ConfigSource {
	return &ViperSource{}
}

// Load reads and parses the configuration file using Viper, then validates it.
func (vs *ViperSource) Load(filePath string, logger *slog.Logger) (*core.Config, error) {
	v := viper.New()
	v.SetConfigFile(filePath)

	// Allow reading environment variables
	v.SetEnvPrefix("MIXY")
	v.AutomaticEnv()
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_", "-", "_")) // Handle more chars

	logger = logger.With(slog.String("config_file", filePath))
	logger.Debug("Attempting to read configuration file")

	if err := v.ReadInConfig(); err != nil {
		var viperErr viper.ConfigFileNotFoundError
		if errors.As(err, &viperErr) {
			return nil, core.NewConfigurationError("config file not found", err, slog.String("path", filePath))
		}
		return nil, core.NewConfigurationError("failed to read config file", err, slog.String("path", filePath))
	}

	var cfg core.Config
	// Set default version *before* unmarshalling if version is missing in the file
	// This allows validation to pass if the file omits version but matches the current structure.
	// A stricter approach would require the version field explicitly.
	v.SetDefault("version", core.MixyConfigVersion)

	if err := v.Unmarshal(&cfg); err != nil {
		return nil, core.NewConfigurationError("failed to unmarshal config file", err, slog.String("path", filePath))
	}

	logger.Debug("Configuration file unmarshalled", slog.Any("raw_config", cfg)) // Log raw for debug

	// Validate the loaded configuration structure
	if err := cfg.Validate(); err != nil {
		// Validation error already includes context
		logger.Error("Configuration validation failed", slog.Any("error", err))
		return nil, err // Return the validation error directly
	}

	logger.Info("Configuration loaded and validated successfully")
	logger.Debug("Validated Configuration Details",
		slog.String("version", cfg.Version),
		slog.Int("template_count", len(cfg.Templates)),
		slog.Int("hook_count", len(cfg.Hooks)),
		slog.Any("default_variables", cfg.Variables), // Be careful logging sensitive vars
		slog.String("default_output", cfg.Output),
		slog.Any("mandatory_variables", cfg.MandatoryVariables),
	)

	return &cfg, nil
}
