// Package steps provides workflow step implementations for Mixy's template processing pipeline.
package steps

import (
	"fmt"
	"log/slog"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// ProcessTemplatesStep loads and processes template files using the configured
// loader resolver and renderer. It handles template resolution, loading of
// template content, and variable substitution.
type ProcessTemplatesStep struct {
	// Resolver determines which loader to use for each template source
	Resolver core.LoaderResolver

	// Renderer processes templates with variables
	Renderer core.TemplateRenderer

	// Options configures template processing behavior
	Options ProcessOptions
}

// ProcessOptions configures how templates are processed.
type ProcessOptions struct {
	// SkipEmptyTemplates indicates whether to skip templates that
	// produce no files instead of treating it as an error
	SkipEmptyTemplates bool

	// StrictVariables indicates whether undefined variables in
	// templates should cause an error
	StrictVariables bool
}

// NewProcessTemplatesStep creates a new ProcessTemplatesStep with the given components.
//
// Parameters:
//   - resolver: The LoaderResolver for determining template loaders
//   - renderer: The TemplateRenderer for processing templates
//   - options: Optional configuration for processing behavior
//
// Returns:
//   - *ProcessTemplatesStep: The configured step
//
// Panics if resolver or renderer is nil, as both are required for operation.
func NewProcessTemplatesStep(resolver core.LoaderResolver, renderer core.TemplateRenderer, options ProcessOptions) *ProcessTemplatesStep {
	if resolver == nil {
		panic("template resolver is required")
	}
	if renderer == nil {
		panic("template renderer is required")
	}

	return &ProcessTemplatesStep{
		Resolver: resolver,
		Renderer: renderer,
		Options:  options,
	}
}

// Name returns the step's identifier.
func (s *ProcessTemplatesStep) Name() string {
	return "process_templates"
}

// Execute processes all configured templates using the resolver and renderer.
// It loads template content, applies variables, and stores the results in the context.
func (s *ProcessTemplatesStep) Execute(ctx *core.ProjectContext) error {
	// Input validation
	if ctx == nil {
		return core.NewTemplateRenderError("nil context provided", nil)
	}
	if ctx.Logger == nil {
		return core.NewTemplateRenderError("nil logger in context", nil)
	}
	if ctx.Config == nil {
		return core.NewTemplateRenderError("nil configuration in context", nil)
	}
	if ctx.Variables == nil {
		return core.NewTemplateRenderError("nil variables in context", nil)
	}

	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Processing template sources",
		slog.Int("count", len(ctx.Config.Templates)))

	// Process all template sources
	allProcessedTemplates := make([][]core.TemplateData, 0, len(ctx.Config.Templates))

	for i, templateSource := range ctx.Config.Templates {
		sourceLogger := stepLogger.With(
			slog.Int("template_index", i+1),
			slog.String("source", templateSource.Source),
			slog.String("type", templateSource.Type))

		processed, err := s.processTemplateSource(templateSource, ctx, sourceLogger)
		if err != nil {
			return fmt.Errorf("failed to process template source %d: %w", i+1, err)
		}

		allProcessedTemplates = append(allProcessedTemplates, processed)
	}

	// Store results
	ctx.LoadedData = allProcessedTemplates

	stepLogger.Info("Templates processed successfully",
		slog.Int("total_templates", len(allProcessedTemplates)))

	return nil
}

// processTemplateSource handles the loading and processing of a single template source.
func (s *ProcessTemplatesStep) processTemplateSource(
	ts core.TemplateSource,
	ctx *core.ProjectContext,
	logger *slog.Logger,
) ([]core.TemplateData, error) {
	logger.Info("Processing template source")

	// Resolve appropriate loader
	loader, sourceForLoad, err := s.Resolver.Resolve(ts, logger)
	if err != nil {
		logger.Error("Failed to resolve template loader",
			slog.Any("error", err))
		return nil, fmt.Errorf("loader resolution failed: %w", err)
	}

	logger.Debug("Template loader selected",
		slog.String("loader_type", fmt.Sprintf("%T", loader)),
		slog.String("load_source", sourceForLoad))

	// Load template content
	template, err := loader.Load(sourceForLoad, ctx)
	if err != nil {
		logger.Error("Failed to load template definition",
			slog.Any("error", err))
		return nil, fmt.Errorf("template loading failed: %w", err)
	}

	rawFiles, err := template.Load(ctx)
	if err != nil {
		logger.Error("Failed to load template content",
			slog.Any("error", err))
		return nil, fmt.Errorf("content loading failed: %w", err)
	}

	logger.Debug("Template content loaded",
		slog.Int("file_count", len(rawFiles)))

	// Process template files
	processed, err := s.processTemplateFiles(rawFiles, ctx, logger)
	if err != nil {
		return nil, err
	}

	// Validate results
	if len(processed) == 0 && !s.Options.SkipEmptyTemplates {
		return nil, core.NewTemplateRenderError(
			"template produced no files",
			nil,
			slog.String("source", ts.Source))
	}

	logger.Info("Template source processed successfully",
		slog.Int("file_count", len(processed)))

	return processed, nil
}

// processTemplateFiles applies the renderer to each template file.
func (s *ProcessTemplatesStep) processTemplateFiles(
	files []core.TemplateData,
	ctx *core.ProjectContext,
	logger *slog.Logger,
) ([]core.TemplateData, error) {
	logger.Debug("Processing template files",
		slog.Int("file_count", len(files)))

	processed := make([]core.TemplateData, 0, len(files))

	for _, file := range files {
		fileLogger := logger.With(slog.String("file", file.Path()))
		fileLogger.Debug("Processing file")

		result, err := s.Renderer.Render(file, ctx.Variables, ctx)
		if err != nil {
			fileLogger.Error("Failed to render template file",
				slog.Any("error", err))
			return nil, fmt.Errorf("failed to render %s: %w", file.Path(), err)
		}

		processed = append(processed, result)
		fileLogger.Debug("File processed successfully")
	}

	return processed, nil
}
