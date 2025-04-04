// internal/io/disk_writer.go
package io

import (
	"log/slog" // Use slog
	"os"
	"path/filepath"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// DiskWriter writes the project structure to the local filesystem.
type DiskWriter struct{}

// NewDiskWriter creates a new DiskWriter instance.
func NewDiskWriter() core.OutputWriter {
	return &DiskWriter{}
}

// Write creates directories and files at the destination path.
func (w *DiskWriter) Write(destination string, data []core.TemplateData, ctx *core.ProjectContext) error {
	logger := ctx.Logger.With(slog.String("component", "disk_writer"), slog.String("destination", destination))
	logger.Info("Starting project output writing", slog.Int("file_count", len(data)))

	logger.Debug("Ensuring output directory exists")
	err := os.MkdirAll(destination, 0755) // Base directory mode
	if err != nil {
		logger.Error("Failed to create output base directory", slog.Any("error", err))
		return core.NewIOError("failed to create output directory", err, slog.String("path", destination))
	}

	for _, fileData := range data {
		relativePath := fileData.Path()
		targetPath := filepath.Join(destination, relativePath)
		targetDir := filepath.Dir(targetPath)
		fileLogger := logger.With(slog.String("relative_path", relativePath), slog.String("target_path", targetPath))

		// Ensure subdirectory exists before writing file
		// Skip if targetDir is the same as destination (already created)
		if targetDir != destination {
			fileLogger.Debug("Ensuring subdirectory exists", slog.String("dir", targetDir))
			if err := os.MkdirAll(targetDir, 0755); err != nil { // Subdirectory mode
				fileLogger.Error("Failed to create subdirectory for file", slog.Any("error", err))
				return core.NewIOError("failed to create directory for file", err, slog.String("directory", targetDir), slog.String("file", relativePath))
			}
		}

		// Get content
		content, err := fileData.Content()
		if err != nil {
			fileLogger.Error("Failed to get file content before writing", slog.Any("error", err))
			return core.NewIOError("failed to get file content", err, slog.String("file", relativePath))
		}

		// Write the file using its specific mode
		mode := fileData.Mode()
		fileLogger.Info("Writing file", slog.Any("mode", mode), slog.Int("size", len(content)))
		if err := os.WriteFile(targetPath, content, mode); err != nil {
			fileLogger.Error("Failed to write file", slog.Any("error", err))
			return core.NewIOError("failed to write file", err, slog.String("path", targetPath))
		}
	}

	logger.Info("Project output writing complete.")
	return nil
}
