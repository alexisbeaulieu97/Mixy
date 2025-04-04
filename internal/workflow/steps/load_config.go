// Package steps provides workflow step implementations for Mixy's template processing pipeline.
package steps

import (
	"fmt"
	"log/slog"
	"path/filepath"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// LoadConfigStep loads and validates the Mixy configuration file.
// It uses a ConfigSource to read and parse the configuration,
// then validates the configuration before storing it in the context.
type LoadConfigStep struct {
	// ConfigSource is responsible for loading and parsing the configuration
	ConfigSource core.ConfigSource
}

// NewLoadConfigStep creates a new LoadConfigStep with the given config source.
//
// Parameters:
//   - source: The ConfigSource to use for loading configuration
//
// Returns:
//   - *LoadConfigStep: The configured step
//
// Panics if source is nil, as it's required for operation.
func NewLoadConfigStep(source core.ConfigSource) *LoadConfigStep {
	if source == nil {
		panic("config source is required")
	}
	return &LoadConfigStep{ConfigSource: source}
}

// Name returns the step's identifier.
func (s *LoadConfigStep) Name() string {
	return "load_config"
}

// Execute loads and validates the configuration file.
// It ensures the config file exists, is readable, and contains valid configuration.
func (s *LoadConfigStep) Execute(ctx *core.ProjectContext) error {
	// Input validation
	if ctx == nil {
		return core.NewConfigurationError("nil context provided", nil)
	}
	if ctx.Logger == nil {
		return core.NewConfigurationError("nil logger in context", nil)
	}
	if ctx.ConfigFilePath == "" {
		return core.NewConfigurationError("empty config file path", nil)
	}

	stepLogger := ctx.Logger.With(
		slog.String("step", s.Name()),
		slog.String("config_file", ctx.ConfigFilePath))

	stepLogger.Info("Loading configuration file")

	// Clean and validate path
	configPath := filepath.Clean(ctx.ConfigFilePath)
	if !filepath.IsAbs(configPath) {
		configPath = filepath.Join(filepath.Dir(ctx.ConfigFilePath), configPath)
	}

	// Load configuration
	cfg, err := s.ConfigSource.Load(configPath, stepLogger)
	if err != nil {
		// Add context to error if needed
		if mixyErr, ok := err.(*core.MixyError); !ok {
			err = core.NewConfigurationError(
				fmt.Sprintf("failed to load config file: %s", configPath),
				err,
				slog.String("config_file", configPath))
		} else {
			// Add file path to existing error context
			mixyErr.Context = append(mixyErr.Context,
				slog.String("config_file", configPath))
		}
		stepLogger.Error("Failed to load configuration",
			slog.String("config_file", configPath),
			slog.Any("error", err))
		return err
	}

	// Validate configuration
	if err := cfg.Validate(); err != nil {
		stepLogger.Error("Configuration validation failed",
			slog.Any("error", err))
		return core.NewValidationError(
			"configuration validation failed",
			err,
			slog.String("config_file", configPath))
	}

	// Store in context
	ctx.Config = cfg

	stepLogger.Info("Configuration loaded successfully",
		slog.String("version", cfg.Version),
		slog.Int("template_count", len(cfg.Templates)))

	return nil
}
