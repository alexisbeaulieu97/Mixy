// Package steps provides workflow step implementations for Mixy's template processing pipeline.
package steps

import (
	"fmt"
	"log/slog"
	"os"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// WriteOutputStep writes the processed template files to the specified output directory.
// It handles file permissions, directory creation, and error recovery during writing.
type WriteOutputStep struct {
	// Writer performs the actual file writing operations
	Writer core.OutputWriter

	// Options configures the output writing behavior
	Options WriteOptions
}

// WriteOptions configures how template files are written to disk.
type WriteOptions struct {
	// DefaultFileMode is the fallback permission mode for files
	// that don't specify their own mode
	DefaultFileMode os.FileMode

	// PreserveExecutable indicates whether to maintain executable
	// permissions from source files
	PreserveExecutable bool

	// SkipExisting indicates whether to skip files that already
	// exist in the output directory
	SkipExisting bool

	// BackupExisting indicates whether to create backups of
	// existing files before overwriting
	BackupExisting bool
}

// NewWriteOutputStep creates a new step with the given writer and options.
//
// Parameters:
//   - writer: The OutputWriter to use for file operations
//   - options: Optional configuration for write behavior
//
// Returns:
//   - *WriteOutputStep: The configured step
//
// Panics if writer is nil, as it's required for operation.
func NewWriteOutputStep(writer core.OutputWriter, options WriteOptions) *WriteOutputStep {
	if writer == nil {
		panic("output writer is required")
	}

	// Set default file mode if not specified
	if options.DefaultFileMode == 0 {
		options.DefaultFileMode = 0644
	}

	return &WriteOutputStep{
		Writer:  writer,
		Options: options,
	}
}

// Name returns the step's identifier.
func (s *WriteOutputStep) Name() string {
	return "write_output"
}

// Execute writes the processed template files to the output directory.
// It ensures all necessary directories exist and handles existing files
// according to the configured options.
func (s *WriteOutputStep) Execute(ctx *core.ProjectContext) error {
	// Input validation
	if ctx == nil {
		return core.NewIOError("nil context provided", nil)
	}
	if ctx.Logger == nil {
		return core.NewIOError("nil logger in context", nil)
	}
	if ctx.MergedData == nil {
		return core.NewIOError("no template data to write (templates must be merged first)", nil)
	}
	if ctx.TempOutputDirectory == "" {
		return core.NewIOError("temporary output directory not set", nil)
	}

	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))

	// Log operation details
	stepLogger.Info("Writing processed template files",
		slog.Int("file_count", len(ctx.MergedData)),
		slog.String("temp_dir", ctx.TempOutputDirectory))

	// Validate backup directory if needed
	if s.Options.BackupExisting {
		if err := s.ensureBackupDirectory(ctx.TempOutputDirectory, stepLogger); err != nil {
			return err
		}
	}

	// Write files with the configured options
	if err := s.writeWithOptions(ctx, stepLogger); err != nil {
		return err
	}

	stepLogger.Info("Template files written successfully",
		slog.Int("file_count", len(ctx.MergedData)))

	return nil
}

// writeWithOptions handles the file writing process with the configured options.
func (s *WriteOutputStep) writeWithOptions(ctx *core.ProjectContext, logger *slog.Logger) error {
	// Apply default file mode to templates if needed
	for _, tmpl := range ctx.MergedData {
		if tmpl == nil {
			return core.NewIOError("encountered nil template data", nil)
		}

		mode := tmpl.Mode()
		if mode == 0 {
			// Use cast to ensure we're working with the interface
			if data, ok := tmpl.(*core.InMemoryTemplateData); ok {
				data.FileMode = s.Options.DefaultFileMode
			}
		}
	}

	// Write files with recovery support
	err := s.Writer.Write(ctx.TempOutputDirectory, ctx.MergedData, ctx)
	if err != nil {
		logger.Error("Failed to write template files",
			slog.Any("error", err))

		if _, ok := err.(*core.MixyError); !ok {
			err = core.NewIOError(
				"failed to write template files",
				err,
				slog.String("temp_dir", ctx.TempOutputDirectory))
		}

		return fmt.Errorf("failed to write output: %w", err)
	}

	return nil
}

// ensureBackupDirectory creates and validates the backup directory.
func (s *WriteOutputStep) ensureBackupDirectory(baseDir string, logger *slog.Logger) error {
	backupDir := baseDir + ".bak"
	logger.Debug("Creating backup directory",
		slog.String("path", backupDir))

	err := os.MkdirAll(backupDir, 0755)
	if err != nil {
		logger.Error("Failed to create backup directory",
			slog.String("path", backupDir),
			slog.Any("error", err))
		return core.NewIOError(
			fmt.Sprintf("failed to create backup directory: %s", backupDir),
			err)
	}

	return nil
}
