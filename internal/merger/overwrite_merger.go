// internal/merger/overwrite_merger.go
package merger

import (
	"log/slog" // Use slog

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
	logger := ctx.Logger.With(slog.String("component", "overwrite_merger"))
	logger.Info("Starting template merge process", slog.Int("template_source_count", len(templates)))
	finalFiles := make(map[string]core.TemplateData) // Use map for easy overwriting by path

	for i, templateFiles := range templates {
		sourceLogger := logger.With(slog.Int("source_index", i))
		sourceLogger.Debug("Merging files from template source")
		for _, fileData := range templateFiles {
			filePath := fileData.Path()
			fileLogger := sourceLogger.With(slog.String("relative_path", filePath))
			if existing, ok := finalFiles[filePath]; ok {
				fileLogger.Warn("File conflict: Overwriting file from previous source.", slog.Any("existing_mode", existing.Mode()), slog.Any("new_mode", fileData.Mode()))
				// Add more details if needed, like which source index it came from previously
			} else {
				fileLogger.Debug("Adding new file.")
			}
			finalFiles[filePath] = fileData // Overwrite or add
		}
	}

	// Convert map back to slice
	result := make([]core.TemplateData, 0, len(finalFiles))
	for _, data := range finalFiles {
		result = append(result, data)
	}

	logger.Info("Template merging complete", slog.Int("final_file_count", len(result)))
	return result, nil
}
