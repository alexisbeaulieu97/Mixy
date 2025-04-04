// internal/workflow/steps/load_config.go
package steps

import (
	"log/slog"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

type LoadConfigStep struct {
	ConfigSource core.ConfigSource
}

func (s *LoadConfigStep) Name() string { return "load_config" }

func (s *LoadConfigStep) Execute(ctx *core.ProjectContext) error {
	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Executing step")

	if s.ConfigSource == nil {
		panic("LoadConfigStep requires a non-nil ConfigSource") // Or return error
	}

	cfg, err := s.ConfigSource.Load(ctx.ConfigFilePath, stepLogger)
	if err != nil {
		// Error from Load should already be structured
		stepLogger.Error("Step failed", slog.Any("error", err))
		return err // Return error directly
	}

	ctx.Config = cfg // Store loaded config in context
	stepLogger.Info("Step completed successfully")
	return nil
}
