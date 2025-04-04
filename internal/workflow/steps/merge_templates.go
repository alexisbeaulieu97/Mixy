// Package steps provides workflow step implementations for Mixy's template processing pipeline.
package steps

import (
	"fmt"
	"log/slog"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// MergeTemplatesStep combines multiple processed templates into a final set
// of template data. It uses a TemplateMerger to resolve conflicts and combine
// overlapping templates in a consistent way.
type MergeTemplatesStep struct {
	// Merger is responsible for combining multiple templates
	Merger core.TemplateMerger

	// Options can be used to configure the merge behavior
	Options MergeOptions
}

// MergeOptions configures how templates are merged.
type MergeOptions struct {
	// SkipEmpty indicates whether to skip empty templates
	// instead of treating them as errors
	SkipEmpty bool

	// AllowOverwrite indicates whether later templates can
	// overwrite files from earlier templates
	AllowOverwrite bool
}

// NewMergeTemplatesStep creates a new MergeTemplatesStep with the given merger and options.
//
// Parameters:
//   - merger: The TemplateMerger to use for combining templates
//   - options: Optional configuration for merge behavior
//
// Returns:
//   - *MergeTemplatesStep: The configured step
//
// Panics if merger is nil, as it's required for operation.
func NewMergeTemplatesStep(merger core.TemplateMerger, options MergeOptions) *MergeTemplatesStep {
	if merger == nil {
		panic("template merger is required")
	}

	return &MergeTemplatesStep{
		Merger:  merger,
		Options: options,
	}
}

// Name returns the step's identifier.
func (s *MergeTemplatesStep) Name() string {
	return "merge_templates"
}

// Execute merges multiple processed templates into a final set of template data.
// It validates input data, combines templates using the configured merger,
// and stores the result in the context.
func (s *MergeTemplatesStep) Execute(ctx *core.ProjectContext) error {
	// Input validation
	if ctx == nil {
		return core.NewTemplateMergeError("nil context provided", nil)
	}
	if ctx.Logger == nil {
		return core.NewTemplateMergeError("nil logger in context", nil)
	}
	if ctx.LoadedData == nil {
		return core.NewTemplateMergeError(
			"no template data to merge (templates must be processed first)",
			nil)
	}

	stepLogger := ctx.Logger.With(
		slog.String("step", s.Name()))

	stepLogger.Info("Merging processed templates",
		slog.Int("template_count", len(ctx.LoadedData)))

	// Validate template data
	if err := s.validateTemplateData(ctx.LoadedData, stepLogger); err != nil {
		return err
	}

	// Perform merge operation
	finalProjectData, err := s.Merger.Merge(ctx.LoadedData, ctx)
	if err != nil {
		stepLogger.Error("Failed to merge templates",
			slog.Any("error", err))
		return core.NewTemplateMergeError(
			"failed to merge templates",
			err,
			slog.Int("template_count", len(ctx.LoadedData)))
	}

	// Validate result
	if finalProjectData == nil {
		return core.NewTemplateMergeError(
			"merger returned nil result",
			nil)
	}
	if len(finalProjectData) == 0 && !s.Options.SkipEmpty {
		return core.NewTemplateMergeError(
			"merger produced empty result",
			nil,
			slog.Int("input_template_count", len(ctx.LoadedData)))
	}

	// Store result and log success
	ctx.MergedData = finalProjectData

	stepLogger.Info("Templates merged successfully",
		slog.Int("input_template_count", len(ctx.LoadedData)),
		slog.Int("output_file_count", len(finalProjectData)))

	return nil
}

// validateTemplateData performs validation checks on the input template data.
func (s *MergeTemplatesStep) validateTemplateData(data [][]core.TemplateData, logger *slog.Logger) error {
	if len(data) == 0 {
		return core.NewTemplateMergeError(
			"no templates to merge",
			nil)
	}

	for i, templateSet := range data {
		if templateSet == nil {
			return core.NewTemplateMergeError(
				fmt.Sprintf("template set %d is nil", i+1),
				nil)
		}
		if len(templateSet) == 0 && !s.Options.SkipEmpty {
			return core.NewTemplateMergeError(
				fmt.Sprintf("template set %d is empty", i+1),
				nil)
		}

		// Check for nil entries
		for j, entry := range templateSet {
			if entry == nil {
				return core.NewTemplateMergeError(
					fmt.Sprintf("nil entry in template set %d at index %d", i+1, j),
					nil)
			}
		}
	}

	return nil
}
