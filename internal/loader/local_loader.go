package loader

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// LocalLoader loads templates from the local filesystem.
type LocalLoader struct{}

// NewLocalLoader creates a new LocalLoader.
func NewLocalLoader() core.TemplateLoader {
	return &LocalLoader{}
}

// Supports checks if the source looks like a local path.
func (l *LocalLoader) Supports(source string) bool {
	// Basic check: does it exist on disk? More robust checks needed later.
	_, err := os.Stat(source)
	return err == nil
}

// Load creates a LocalTemplate representation.
func (l *LocalLoader) Load(source string, ctx *core.ProjectContext) (core.Template, error) {
	absSource, err := filepath.Abs(source)
	if err != nil {
		return nil, fmt.Errorf("failed to get absolute path for local source '%s': %w", source, err)
	}
	_, err = os.Stat(absSource)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("local template source not found: %s", absSource)
		}
		return nil, fmt.Errorf("failed to stat local template source '%s': %w", absSource, err)
	}
	return &LocalTemplate{BasePath: absSource}, nil
}

// LocalTemplate represents a template stored on the local filesystem.
type LocalTemplate struct {
	BasePath string // Absolute path to the template root directory or file
}

// Source returns the base path.
func (t *LocalTemplate) Source() string {
	return t.BasePath
}

// Load reads files/directories from the local path.
func (t *LocalTemplate) Load(ctx *core.ProjectContext) ([]core.TemplateData, error) {
	fmt.Printf("  Loading local template from: %s\n", t.BasePath) // Debugging
	var files []core.TemplateData

	err := filepath.WalkDir(t.BasePath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err // Propagate errors (e.g., permission denied)
		}

		// Calculate relative path for project structure
		relativePath, err := filepath.Rel(t.BasePath, path)
		if err != nil {
			return fmt.Errorf("failed to calculate relative path for %s: %w", path, err)
		}

		// Skip the root directory itself
		if relativePath == "." {
			return nil
		}

		// We only care about files for now, directories will be created by the OutputWriter
		if !d.IsDir() {
			fmt.Printf("    Found file: %s (relative: %s)\n", path, relativePath) // Debugging
			content, err := os.ReadFile(path)
			if err != nil {
				return fmt.Errorf("failed to read file %s: %w", path, err)
			}
			// Use the InMemory implementation for now
			files = append(files, core.NewInMemoryTemplateData(relativePath, content))
		} else {
			fmt.Printf("    Found directory: %s (relative: %s) - skipping content loading\n", path, relativePath) // Debugging
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("error walking template directory '%s': %w", t.BasePath, err)
	}

	return files, nil
}
