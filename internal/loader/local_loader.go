// internal/loader/local_loader.go
package loader

import (
	"io/fs"
	"log/slog" // Use slog
	"os"
	"path/filepath"
	"strings"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// LocalLoader loads templates from the local filesystem.
type LocalLoader struct{}

// NewLocalLoader creates a new LocalLoader.
func NewLocalLoader() core.TemplateLoader {
	return &LocalLoader{}
}

// Supports checks if the source looks like a local path that exists.
func (l *LocalLoader) Supports(source string) bool {
	// Basic check: does it exist on disk? This might interact poorly with plugins
	// if plugin source format looks like a path. Rely on Workflow ordering?
	// Or make the check more specific (e.g., avoid "plugin:" prefix).
	if strings.HasPrefix(source, "plugin:") {
		return false // Explicitly don't support plugin sources
	}
	_, err := os.Stat(source)
	// Consider logging the Stat error here for debugging? Maybe too noisy.
	return err == nil
}

// Load creates a LocalTemplate representation.
func (l *LocalLoader) Load(source string, ctx *core.ProjectContext) (core.Template, error) {
	logger := ctx.Logger.With(slog.String("component", "local_loader"), slog.String("source", source))
	logger.Debug("Attempting to load local template")

	absSource, err := filepath.Abs(source)
	if err != nil {
		logger.Error("Failed to get absolute path", slog.Any("error", err))
		return nil, core.NewTemplateLoadError("failed to get absolute path", err, slog.String("source", source))
	}
	logger = logger.With(slog.String("absolute_source", absSource)) // Add abs path to context

	info, err := os.Stat(absSource)
	if err != nil {
		if os.IsNotExist(err) {
			logger.Error("Local template source not found", slog.Any("error", err))
			return nil, core.NewTemplateLoadError("local template source not found", err, slog.String("path", absSource))
		}
		logger.Error("Failed to stat local template source", slog.Any("error", err))
		return nil, core.NewTemplateLoadError("failed to stat local template source", err, slog.String("path", absSource))
	}

	logger.Debug("Local template source found", slog.Bool("is_dir", info.IsDir()))
	return &LocalTemplate{BasePath: absSource, Logger: logger}, nil // Pass logger
}

// LocalTemplate represents a template stored on the local filesystem.
type LocalTemplate struct {
	BasePath string // Absolute path to the template root directory or file
	Logger   *slog.Logger
}

// Source returns the base path.
func (t *LocalTemplate) Source() string {
	return t.BasePath
}

// Load reads files/directories from the local path.
func (t *LocalTemplate) Load(ctx *core.ProjectContext) ([]core.TemplateData, error) {
	t.Logger.Info("Loading local template content")
	var files []core.TemplateData
	fileCount := 0
	dirCount := 0

	err := filepath.WalkDir(t.BasePath, func(path string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			// Handle errors during walk (e.g., permission denied)
			t.Logger.Error("Error during directory walk", slog.String("path", path), slog.Any("error", walkErr))
			// Decide whether to stop walking or just skip the entry
			return core.NewTemplateLoadError("error walking template directory", walkErr, slog.String("path", path))
		}

		// Calculate relative path for project structure
		relativePath, err := filepath.Rel(t.BasePath, path)
		if err != nil {
			// This should ideally not happen if BasePath is ancestor of path
			t.Logger.Error("Failed to calculate relative path", slog.String("base", t.BasePath), slog.String("path", path), slog.Any("error", err))
			return core.NewTemplateLoadError("failed to calculate relative path", err, slog.String("base", t.BasePath), slog.String("path", path))
		}

		// Skip the root directory itself
		if relativePath == "." {
			return nil
		}

		fileLogger := t.Logger.With(slog.String("relative_path", relativePath), slog.String("full_path", path))

		if d.IsDir() {
			dirCount++
			fileLogger.Debug("Found directory (content loading skipped)")
			// Directories will be created by the OutputWriter based on file paths
		} else {
			fileCount++
			fileLogger.Debug("Found file")
			content, err := os.ReadFile(path)
			if err != nil {
				fileLogger.Error("Failed to read file content", slog.Any("error", err))
				// Return error to stop the walk
				return core.NewTemplateLoadError("failed to read template file", err, slog.String("path", path))
			}

			// Get file mode
			info, err := d.Info() // Use info from DirEntry
			if err != nil {
				fileLogger.Warn("Failed to get file info for mode, using default", slog.Any("error", err))
				info = nil // Ensure info is nil if error occurs
			}
			var mode fs.FileMode = 0644 // Default mode
			if info != nil {
				mode = info.Mode()
			}

			// Use the InMemory implementation
			files = append(files, core.NewInMemoryTemplateData(relativePath, content, mode))
		}

		return nil // Continue walking
	})

	if err != nil {
		// Error already logged during walk or wrapping failed reads
		t.Logger.Error("Template content loading failed.", slog.Any("error", err))
		return nil, err // Return the wrapped error from WalkDir/ReadFile
	}

	t.Logger.Info("Local template content loaded successfully", slog.Int("files_loaded", fileCount), slog.Int("directories_found", dirCount))
	return files, nil
}
