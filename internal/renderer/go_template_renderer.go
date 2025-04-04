// internal/renderer/go_template_renderer.go
package renderer

import (
	"bytes"
	"log/slog" // Use slog
	"text/template"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// GoTemplateRenderer uses Go's text/template engine.
type GoTemplateRenderer struct{}

// NewGoTemplateRenderer creates a new renderer instance.
func NewGoTemplateRenderer() core.TemplateRenderer {
	return &GoTemplateRenderer{}
}

// Render applies variables using text/template.
func (r *GoTemplateRenderer) Render(raw core.TemplateData, variables map[string]interface{}, ctx *core.ProjectContext) (core.TemplateData, error) {
	logger := ctx.Logger.With(slog.String("component", "go_template_renderer"), slog.String("template_path", raw.Path()))
	logger.Debug("Rendering template file")

	rawContentBytes, err := raw.Content()
	if err != nil {
		logger.Error("Failed to get raw template content", slog.Any("error", err))
		return nil, core.NewTemplateRenderError("failed to get raw content", err, slog.String("path", raw.Path()))
	}
	rawContent := string(rawContentBytes)

	// Add FuncMap here later for template helper functions
	// funcs := template.FuncMap{ /* ... */ }

	// Create a new template and parse content - includes syntax validation.
	tmpl, err := template.New(raw.Path()).Option("missingkey=error").Parse(rawContent) // Use Option("missingkey=error")? Or "missingkey=zero"? Error is safer.
	// tmpl, err := template.New(raw.Path()).Funcs(funcs).Option("missingkey=error").Parse(rawContent) // With funcs

	if err != nil {
		// This error indicates a syntax error in the template itself.
		logger.Error("Failed to parse template syntax", slog.Any("error", err))
		// Return a structured error indicating it's a template content issue.
		return nil, core.NewTemplateRenderError("template syntax error", err, slog.String("path", raw.Path()))
	}

	var renderedContent bytes.Buffer
	// Execute the template
	if err := tmpl.Execute(&renderedContent, variables); err != nil {
		// This error usually means a variable used in the template was missing (if missingkey=error)
		// or an execution-time issue occurred in a template function.
		logger.Error("Failed to execute template", slog.Any("error", err))
		return nil, core.NewTemplateRenderError("template execution failed", err, slog.String("path", raw.Path()), slog.Any("variables", variables)) // Log vars carefully
	}

	logger.Debug("Template rendering successful")
	// Return new data structure with rendered content, preserving original path and mode.
	return core.NewInMemoryTemplateData(raw.Path(), renderedContent.Bytes(), raw.Mode()), nil
}
