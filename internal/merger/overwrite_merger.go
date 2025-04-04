package merger

import (
	"fmt"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// OverwriteMerger implements a simple merge strategy: last template wins on conflict.
type OverwriteMerger struct{}

// NewOverwriteMerger creates a new merger instance.
func NewOverwriteMerger() core.TemplateMerger {
	return &OverwriteMerger{}
}

// Merge combines templates, overwriting files with the same path from later templates.
func (m *OverwriteMerger) Merge(templates [][]core.TemplateData, ctx *core.ProjectContext) ([]core.TemplateData, error) {
	finalFiles := make(map[string]core.TemplateData) // Use map for easy overwriting by path

	for i, templateFiles := range templates {
		fmt.Printf("  Merging files from template source %d\n", i+1) // Debugging
		for _, fileData := range templateFiles {
			filePath := fileData.Path()
			if existing, ok := finalFiles[filePath]; ok {
				fmt.Printf("    Conflict: Overwriting '%s' from previous template source.\n", filePath) // Debugging
				_ = existing                                                                            // Keep compiler happy if not used further
			} else {
				fmt.Printf("    Adding new file '%s'.\n", filePath) // Debugging
			}
			finalFiles[filePath] = fileData
		}
	}

	// Convert map back to slice
	result := make([]core.TemplateData, 0, len(finalFiles))
	for _, data := range finalFiles {
		result = append(result, data)
	}

	return result, nil
}
