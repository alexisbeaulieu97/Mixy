// internal/workflow/steps/create_temp_dir.go
package steps

import (
	"log/slog"
	"os"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

type CreateTempDirStep struct{}

func (s *CreateTempDirStep) Name() string { return "create_temp_dir" }

func (s *CreateTempDirStep) Execute(ctx *core.ProjectContext) error {
	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Executing step")

	// Create temp dir in the OS default temp location or relative to final output?
	// OS default is usually safer regarding permissions and cleanup.
	// Prefix with "mixy-" for easier identification.
	tempDir, err := os.MkdirTemp("", "mixy-output-*")
	if err != nil {
		stepLogger.Error("Failed to create temporary output directory", slog.Any("error", err))
		return core.NewIOError("failed to create temporary output directory", err)
	}

	ctx.TempOutputDirectory = tempDir // Store path in context
	stepLogger.Info("Temporary output directory created successfully", slog.String("temp_dir", tempDir))
	return nil
}
