// internal/workflow/steps/write_output.go
package steps

import (
	"log/slog"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

type WriteOutputStep struct {
	Writer core.OutputWriter
}

func (s *WriteOutputStep) Name() string { return "write_output" }

func (s *WriteOutputStep) Execute(ctx *core.ProjectContext) error {
	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Executing step")

	if s.Writer == nil {
		panic("WriteOutputStep requires a non-nil OutputWriter")
	}
	if ctx.MergedData == nil {
		return core.NewError(core.ErrorTypeUnknown, "cannot write output before templates are merged", nil)
	}
	// --- Write to Temp Dir ---
	if ctx.TempOutputDirectory == "" {
		return core.NewError(core.ErrorTypeUnknown, "temporary output directory not created before writing output", nil)
	}
	targetDir := ctx.TempOutputDirectory
	stepLogger = stepLogger.With(slog.String("target_temp_dir", targetDir))
	// --- End Temp Dir Change ---

	stepLogger.Info("Writing project structure to temporary directory")
	err := s.Writer.Write(targetDir, ctx.MergedData, ctx) // Use targetDir
	if err != nil {
		stepLogger.Error("Step failed", slog.Any("error", err))
		// Error from Write should already be structured
		return err
	}

	stepLogger.Info("Step completed successfully")
	return nil
}
