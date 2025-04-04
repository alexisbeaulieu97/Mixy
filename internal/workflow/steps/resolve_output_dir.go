// internal/workflow/steps/resolve_output_dir.go
package steps

import (
	"log/slog"
	"path/filepath"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

type ResolveOutputDirStep struct{}

func (s *ResolveOutputDirStep) Name() string { return "resolve_output_dir" }

func (s *ResolveOutputDirStep) Execute(ctx *core.ProjectContext) error {
	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Executing step")

	if ctx.Config == nil {
		return core.NewError(core.ErrorTypeConfiguration, "cannot resolve output directory before config is loaded", nil)
	}

	outputDir := "." // Default
	if ctx.Config.Output != "" {
		outputDir = ctx.Config.Output
		stepLogger.Debug("Using output directory from config", slog.String("dir", outputDir))
	}
	// Flag override happens here - ctx.OutputDirectory holds the flag value initially
	if ctx.OutputDirectory != "" {
		outputDir = ctx.OutputDirectory
		stepLogger.Info("Overriding output directory from flag", slog.String("dir", outputDir))
	}

	absOutputDir, err := filepath.Abs(outputDir)
	if err != nil {
		stepLogger.Error("Failed to determine absolute output path", slog.String("path", outputDir), slog.Any("error", err))
		return core.NewIOError("failed to determine absolute output path", err, slog.String("path", outputDir))
	}

	ctx.OutputDirectory = absOutputDir // Update context with absolute path
	stepLogger.Info("Step completed successfully", slog.String("absolute_path", ctx.OutputDirectory))
	return nil
}
