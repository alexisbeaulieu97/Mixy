// internal/workflow/steps/process_templates.go
package steps

import (
	// "fmt" // No longer needed
	"fmt"
	"log/slog"
	// "strings" // No longer needed

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

type ProcessTemplatesStep struct {
	// --- Inject Resolver instead of Loaders ---
	Resolver core.LoaderResolver
	Renderer core.TemplateRenderer
}

func (s *ProcessTemplatesStep) Name() string { return "process_templates" }

func (s *ProcessTemplatesStep) Execute(ctx *core.ProjectContext) error {
	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Executing step")

	// --- Update Panics/Checks ---
	if s.Resolver == nil {
		panic("ProcessTemplatesStep requires a non-nil LoaderResolver")
	}
	if s.Renderer == nil {
		panic("ProcessTemplatesStep requires a non-nil TemplateRenderer")
	}
	if ctx.Config == nil || ctx.Variables == nil {
		return core.NewError(core.ErrorTypeConfiguration, "cannot process templates before config is loaded and variables are resolved", nil)
	}

	allProcessedTemplates := make([][]core.TemplateData, 0, len(ctx.Config.Templates))
	stepLogger.Info("Processing template sources", slog.Int("count", len(ctx.Config.Templates)))

	for i, ts := range ctx.Config.Templates {
		sourceLogger := stepLogger.With(slog.Int("template_index", i), slog.String("original_source", ts.Source), slog.String("type_hint", ts.Type))
		sourceLogger.Info("Processing template source")

		// --- Use Resolver ---
		selectedLoader, sourceForLoad, err := s.Resolver.Resolve(ts, sourceLogger)
		if err != nil {
			sourceLogger.Error("Failed to resolve loader", slog.Any("error", err))
			return err // Return error from resolver
		}
		// Resolver handles logging success/details
		sourceLogger.Info("Selected loader for template source", slog.String("loader_type", fmt.Sprintf("%T", selectedLoader)), slog.String("load_source", sourceForLoad))
		// --- End Resolver Usage ---

		// --- Load ---
		template, err := selectedLoader.Load(sourceForLoad, ctx) // Use sourceForLoad
		if err != nil {
			sourceLogger.Error("Failed to load template definition", slog.Any("error", err))
			return err
		}
		rawTemplateFiles, err := template.Load(ctx)
		if err != nil {
			sourceLogger.Error("Failed to load template content", slog.Any("error", err))
			return err
		}
		sourceLogger.Info("Template content loaded", slog.Int("file_count", len(rawTemplateFiles)))

		// --- Render ---
		sourceLogger.Debug("Rendering template files")
		processedTemplateFiles := make([]core.TemplateData, 0, len(rawTemplateFiles))
		for _, rawFile := range rawTemplateFiles {
			fileLogger := sourceLogger.With(slog.String("relative_path", rawFile.Path()))
			fileLogger.Debug("Rendering file")
			processedFile, err := s.Renderer.Render(rawFile, ctx.Variables, ctx)
			if err != nil {
				fileLogger.Error("Failed to render template file", slog.Any("error", err))
				return err
			}
			processedTemplateFiles = append(processedTemplateFiles, processedFile)
		}
		allProcessedTemplates = append(allProcessedTemplates, processedTemplateFiles)
		sourceLogger.Info("Template source processing complete")
	} // End template source loop

	ctx.LoadedData = allProcessedTemplates
	stepLogger.Info("Step completed successfully")
	return nil
}
