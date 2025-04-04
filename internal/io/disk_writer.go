package io

import (
	"fmt"
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
func (w *DiskWriter) Write(destination string, data []core.TemplateData) error {
	fmt.Printf("Ensuring output directory exists: %s\n", destination) // Debugging
	err := os.MkdirAll(destination, 0755)                             // Ensure base directory exists
	if err != nil {
		return fmt.Errorf("failed to create output directory '%s': %w", destination, err)
	}

	for _, fileData := range data {
		targetPath := filepath.Join(destination, fileData.Path())
		targetDir := filepath.Dir(targetPath)

		// Ensure subdirectory exists
		if err := os.MkdirAll(targetDir, 0755); err != nil {
			return fmt.Errorf("failed to create directory '%s' for file '%s': %w", targetDir, fileData.Path(), err)
		}

		// Get content
		content, err := fileData.Content()
		if err != nil {
			return fmt.Errorf("failed to get content for '%s': %w", fileData.Path(), err)
		}

		// Write the file
		// Consider adding file mode preservation later using fileData.Mode()
		fmt.Printf("  Writing file: %s\n", targetPath)                  // Debugging
		if err := os.WriteFile(targetPath, content, 0644); err != nil { // Default mode 0644
			return fmt.Errorf("failed to write file '%s': %w", targetPath, err)
		}
	}

	return nil
}
