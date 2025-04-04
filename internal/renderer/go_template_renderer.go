package renderer

import (
	"bytes"
	"fmt"
	"text/template" // Using Go's standard templating

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// GoTemplateRenderer uses Go's text/template engine.
type GoTemplateRenderer struct{}

// NewGoTemplateRenderer creates a new renderer instance.
func NewGoTemplateRenderer() core.TemplateRenderer {
	return &GoTemplateRenderer{}
}

// Render applies variables using text/template.
func (r *GoTemplateRenderer) Render(raw core.TemplateData, variables map[string]interface{}) (core.TemplateData, error) {
	rawContentBytes, err := raw.Content()
	if err != nil {
		return nil, fmt.Errorf("failed to get raw content for %s: %w", raw.Path(), err)
	}
	rawContent := string(rawContentBytes)

	// Create a new template for each file to isolate parsing errors
	// Add FuncMap here later for template helper functions
	tmpl, err := template.New(raw.Path()).Parse(rawContent)
	if err != nil {
		return nil, fmt.Errorf("failed to parse template for '%s': %w", raw.Path(), err)
	}

	var renderedContent bytes.Buffer
	if err := tmpl.Execute(&renderedContent, variables); err != nil {
		return nil, fmt.Errorf("failed to execute template for '%s': %w", raw.Path(), err)
	}

	// Return new data structure with rendered content
	// Keep the original path
	// Using InMemoryTemplateData for simplicity now
	return core.NewInMemoryTemplateData(raw.Path(), renderedContent.Bytes()), nil
}
