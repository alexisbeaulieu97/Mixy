// internal/workflow/steps/merge_templates.go
package steps

import (
	"log/slog"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

type MergeTemplatesStep struct {
	Merger core.TemplateMerger
}

func (s *MergeTemplatesStep) Name() string { return "merge_templates" }

func (s *MergeTemplatesStep) Execute(ctx *core.ProjectContext) error {
	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Executing step")

	if s.Merger == nil {
		panic("MergeTemplatesStep requires a non-nil TemplateMerger")
	}
	if ctx.LoadedData == nil {
		return core.NewError(core.ErrorTypeUnknown, "cannot merge templates before they are processed", nil)
	}

	finalProjectData, err := s.Merger.Merge(ctx.LoadedData, ctx)
	if err != nil {
		stepLogger.Error("Step failed", slog.Any("error", err))
		return core.NewError(core.ErrorTypeTemplateMerge, "failed to merge templates", err)
	}

	ctx.MergedData = finalProjectData // Store result
	stepLogger.Info("Step completed successfully", slog.Int("final_file_count", len(ctx.MergedData)))
	return nil
}
