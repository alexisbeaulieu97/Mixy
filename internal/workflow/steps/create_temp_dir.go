// Package steps provides workflow step implementations for Mixy's template processing pipeline.
package steps

import (
	"fmt"
	"log/slog"
	"os"
	"path/filepath"
	"strings"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

const (
	// tempDirPrefix is prepended to temporary directories for identification
	tempDirPrefix = "mixy-output-"
)

// CreateTempDirStep creates a temporary directory for processing templates.
// This directory will be used to store intermediate files during template
// processing and will be cleaned up by the workflow runner if an error occurs.
type CreateTempDirStep struct {
	// BaseDir optionally specifies where to create the temp directory
	// If empty, the system's default temporary directory is used
	BaseDir string

	// Prefix optionally overrides the default mixy-output- prefix
	// If empty, the default prefix is used
	Prefix string
}

// NewCreateTempDirStep creates a new CreateTempDirStep with optional configuration.
func NewCreateTempDirStep(baseDir string) *CreateTempDirStep {
	return &CreateTempDirStep{
		BaseDir: baseDir,
	}
}

// Name returns the step's identifier.
func (s *CreateTempDirStep) Name() string {
	return "create_temp_dir"
}

// Execute creates a temporary directory and stores its path in the context.
// The directory will be created in either the system temp directory or
// the configured base directory.
func (s *CreateTempDirStep) Execute(ctx *core.ProjectContext) error {
	if ctx == nil {
		return core.NewIOError("nil context provided", nil)
	}
	if ctx.Logger == nil {
		return core.NewIOError("nil logger in context", nil)
	}

	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Creating temporary directory")

	// Determine base directory
	baseDir := s.BaseDir
	if baseDir == "" {
		baseDir = os.TempDir()
	}

	// Ensure base directory exists and is accessible
	if err := s.validateBaseDir(baseDir, stepLogger); err != nil {
		return err
	}

	// Determine prefix
	prefix := s.Prefix
	if prefix == "" {
		prefix = tempDirPrefix
	}
	if !strings.HasSuffix(prefix, "-") {
		prefix = prefix + "-"
	}

	// Create the temporary directory
	tempDir, err := os.MkdirTemp(baseDir, prefix+"*")
	if err != nil {
		stepLogger.Error("Failed to create temporary directory",
			slog.String("base_dir", baseDir),
			slog.String("prefix", prefix),
			slog.Any("error", err))
		return core.NewIOError("failed to create temporary directory", err)
	}

	// Clean up path for consistency
	tempDir = filepath.Clean(tempDir)

	// Store in context and log success
	ctx.TempOutputDirectory = tempDir
	stepLogger.Info("Temporary directory created",
		slog.String("temp_dir", tempDir),
		slog.String("base_dir", baseDir))

	return nil
}

// validateBaseDir ensures the base directory exists and is writable.
func (s *CreateTempDirStep) validateBaseDir(dir string, logger *slog.Logger) error {
	// Check if directory exists
	info, err := os.Stat(dir)
	if err != nil {
		if os.IsNotExist(err) {
			logger.Error("Base directory does not exist",
				slog.String("dir", dir))
			return core.NewIOError(
				fmt.Sprintf("base directory does not exist: %s", dir),
				err)
		}
		logger.Error("Failed to check base directory",
			slog.String("dir", dir),
			slog.Any("error", err))
		return core.NewIOError(
			fmt.Sprintf("failed to check base directory: %s", dir),
			err)
	}

	// Check if it's a directory
	if !info.IsDir() {
		logger.Error("Base path is not a directory",
			slog.String("dir", dir))
		return core.NewIOError(
			fmt.Sprintf("base path is not a directory: %s", dir),
			nil)
	}

	// Check if directory is writable by trying to create a test file
	f, err := os.CreateTemp(dir, ".mixy-write-test-*")
	if err != nil {
		logger.Error("Base directory is not writable",
			slog.String("dir", dir),
			slog.Any("error", err))
		return core.NewIOError(
			fmt.Sprintf("base directory is not writable: %s", dir),
			err)
	}
	f.Close()
	os.Remove(f.Name())

	return nil
}
