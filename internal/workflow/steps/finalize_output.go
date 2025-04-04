// Package steps provides workflow step implementations for Mixy's template processing pipeline.
package steps

import (
	"errors"
	"fmt"
	"io"
	"io/fs"
	"log/slog"
	"os"
	"path/filepath"
	"time"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// FinalizeOutputStep moves the processed template files from the temporary
// directory to their final destination. It handles file conflicts, permissions,
// and cleanup of temporary files.
type FinalizeOutputStep struct {
	// Options configures the finalization behavior
	Options FinalizeOptions
}

// FinalizeOptions configures how output files are finalized.
type FinalizeOptions struct {
	// ExistingDirStrategy determines how to handle an existing output directory
	ExistingDirStrategy ExistingDirStrategy

	// BackupFormat defines the format for backup directory names
	// Default: ".bak-%Y%m%d-%H%M%S"
	BackupFormat string

	// PreserveTemp indicates whether to keep the temporary directory
	// after successful finalization (useful for debugging)
	PreserveTemp bool

	// CustomPerms optionally specifies custom permissions to apply
	// to the final output directory and files
	CustomPerms *fs.FileMode
}

// ExistingDirStrategy defines how to handle existing output directories.
type ExistingDirStrategy int

const (
	// OverwriteExisting removes the existing directory
	OverwriteExisting ExistingDirStrategy = iota

	// BackupExisting moves the existing directory to a backup location
	BackupExisting

	// ErrorIfExists returns an error if the directory exists
	ErrorIfExists

	// MergeWithExisting preserves existing files and adds new ones
	MergeWithExisting
)

// defaultBackupFormat is used when no backup format is specified
const defaultBackupFormat = ".bak-%Y%m%d-%H%M%S"

// NewFinalizeOutputStep creates a new step with the given options.
//
// Parameters:
//   - options: Optional configuration for finalization behavior
//
// Returns:
//   - *FinalizeOutputStep: The configured step
func NewFinalizeOutputStep(options FinalizeOptions) *FinalizeOutputStep {
	// Set default backup format if not specified
	if options.BackupFormat == "" {
		options.BackupFormat = defaultBackupFormat
	}

	return &FinalizeOutputStep{
		Options: options,
	}
}

// Name returns the step's identifier.
func (s *FinalizeOutputStep) Name() string {
	return "finalize_output"
}

// Execute moves the processed files to their final location and performs cleanup.
func (s *FinalizeOutputStep) Execute(ctx *core.ProjectContext) error {
	// Input validation
	if ctx == nil {
		return core.NewIOError("nil context provided", nil)
	}
	if ctx.Logger == nil {
		return core.NewIOError("nil logger in context", nil)
	}
	if ctx.TempOutputDirectory == "" {
		return core.NewIOError("temporary output directory path missing", nil)
	}
	if ctx.OutputDirectory == "" {
		return core.NewIOError("final output directory path missing", nil)
	}

	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Finalizing output",
		slog.String("temp_dir", ctx.TempOutputDirectory),
		slog.String("final_dir", ctx.OutputDirectory))

	// Handle existing directory
	if err := s.handleExistingDirectory(ctx.OutputDirectory, stepLogger); err != nil {
		return fmt.Errorf("failed to handle existing directory: %w", err)
	}

	// Prepare destination directory
	if err := s.prepareDestination(ctx.OutputDirectory, stepLogger); err != nil {
		return fmt.Errorf("failed to prepare destination: %w", err)
	}

	// Copy files to final location
	if err := s.copyOutput(ctx.TempOutputDirectory, ctx.OutputDirectory, stepLogger); err != nil {
		return fmt.Errorf("failed to copy output: %w", err)
	}

	// Cleanup temporary directory
	if err := s.cleanup(ctx, stepLogger); err != nil {
		stepLogger.Error("Failed to cleanup temporary directory",
			slog.Any("error", err))
		// Continue since the copy was successful
	}

	stepLogger.Info("Output finalized successfully")
	return nil
}

// handleExistingDirectory manages any existing directory at the destination path.
func (s *FinalizeOutputStep) handleExistingDirectory(finalDir string, logger *slog.Logger) error {
	info, err := os.Stat(finalDir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil // Directory doesn't exist, nothing to handle
		}
		return fmt.Errorf("failed to check final directory: %w", err)
	}

	if !info.IsDir() {
		return core.NewIOError(
			fmt.Sprintf("output path exists but is not a directory: %s", finalDir),
			nil)
	}

	switch s.Options.ExistingDirStrategy {
	case OverwriteExisting:
		logger.Info("Removing existing directory",
			slog.String("path", finalDir))
		if err := os.RemoveAll(finalDir); err != nil {
			return fmt.Errorf("failed to remove existing directory: %w", err)
		}

	case BackupExisting:
		backupDir := s.generateBackupPath(finalDir)
		logger.Info("Moving existing directory to backup",
			slog.String("backup", backupDir))
		if err := os.Rename(finalDir, backupDir); err != nil {
			return fmt.Errorf("failed to create backup: %w", err)
		}

	case ErrorIfExists:
		return core.NewIOError(
			fmt.Sprintf("output directory already exists: %s", finalDir),
			nil)

	case MergeWithExisting:
		logger.Info("Merging with existing directory",
			slog.String("path", finalDir))
		// No action needed, files will be merged during copy
	}

	return nil
}

// prepareDestination ensures the destination directory and its parent exist.
func (s *FinalizeOutputStep) prepareDestination(finalDir string, logger *slog.Logger) error {
	// Create parent directory
	parentDir := filepath.Dir(finalDir)
	logger.Debug("Creating parent directory",
		slog.String("path", parentDir))

	mode := os.FileMode(0755)
	if s.Options.CustomPerms != nil {
		mode = *s.Options.CustomPerms
	}

	if err := os.MkdirAll(parentDir, mode); err != nil {
		return fmt.Errorf("failed to create parent directory: %w", err)
	}

	return nil
}

// copyOutput moves files from temporary to final location.
func (s *FinalizeOutputStep) copyOutput(tempDir, finalDir string, logger *slog.Logger) error {
	logger.Debug("Starting recursive copy",
		slog.String("from", tempDir),
		slog.String("to", finalDir))

	if err := copyDirectory(tempDir, finalDir, logger); err != nil {
		return fmt.Errorf("failed to copy directory contents: %w", err)
	}

	return nil
}

// cleanup handles post-copy cleanup operations.
func (s *FinalizeOutputStep) cleanup(ctx *core.ProjectContext, logger *slog.Logger) error {
	if s.Options.PreserveTemp {
		logger.Info("Preserving temporary directory",
			slog.String("path", ctx.TempOutputDirectory))
		return nil
	}

	logger.Debug("Removing temporary directory")
	if err := os.RemoveAll(ctx.TempOutputDirectory); err != nil {
		return fmt.Errorf("failed to remove temporary directory: %w", err)
	}

	// Prevent cleanup by workflow runner
	ctx.TempOutputDirectory = ""
	return nil
}

// generateBackupPath creates a unique backup directory path.
func (s *FinalizeOutputStep) generateBackupPath(basePath string) string {
	timestamp := time.Now().Format(s.Options.BackupFormat)
	return fmt.Sprintf("%s%s", basePath, timestamp)
}

// copyDirectory recursively copies directory contents.
func copyDirectory(src, dst string, logger *slog.Logger) error {
	logger.Debug("Walking source directory")

	var copyErr error
	err := filepath.WalkDir(src, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err // Propagate WalkDir errors
		}

		// Get relative path
		relPath, err := filepath.Rel(src, path)
		if err != nil {
			return fmt.Errorf("failed to get relative path: %w", err)
		}
		dstPath := filepath.Join(dst, relPath)

		// Copy the item
		if err := copyItem(path, dstPath, d, logger); err != nil {
			copyErr = err
			return fs.SkipDir // Stop walking on error
		}

		return nil
	})

	// Handle walk errors
	if err != nil && !errors.Is(err, fs.SkipDir) {
		return fmt.Errorf("failed to walk directory: %w", err)
	}

	// Return any copy errors
	if copyErr != nil {
		return copyErr
	}

	return nil
}

// copyItem copies a single file or directory.
func copyItem(src, dst string, entry fs.DirEntry, logger *slog.Logger) error {
	itemLogger := logger.With(
		slog.String("src", src),
		slog.String("dst", dst))

	info, err := entry.Info()
	if err != nil {
		return fmt.Errorf("failed to get file info: %w", err)
	}

	if entry.IsDir() {
		return copyDir(dst, info.Mode(), itemLogger)
	}
	return copyFile(src, dst, info, itemLogger)
}

// copyDir creates a directory with the specified mode.
func copyDir(path string, mode fs.FileMode, logger *slog.Logger) error {
	logger.Debug("Creating directory",
		slog.String("path", path),
		slog.Any("mode", mode))

	if err := os.MkdirAll(path, mode); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	return nil
}

// copyFile copies a single file, preserving mode and handling errors.
func copyFile(src, dst string, info fs.FileInfo, logger *slog.Logger) error {
	logger.Debug("Copying file",
		slog.Int64("size", info.Size()))

	// Open source
	source, err := os.Open(src)
	if err != nil {
		return fmt.Errorf("failed to open source: %w", err)
	}
	defer source.Close()

	// Create destination with temp name
	tmpDst := dst + ".tmp"
	dest, err := os.OpenFile(tmpDst, os.O_RDWR|os.O_CREATE|os.O_TRUNC, info.Mode())
	if err != nil {
		return fmt.Errorf("failed to create destination: %w", err)
	}
	defer func() {
		dest.Close()
		if err != nil {
			os.Remove(tmpDst) // Clean up on error
		}
	}()

	// Copy content
	if _, err := io.Copy(dest, source); err != nil {
		return fmt.Errorf("failed to copy content: %w", err)
	}

	// Sync to disk
	if err := dest.Sync(); err != nil {
		return fmt.Errorf("failed to sync file: %w", err)
	}

	// Close file before rename
	if err := dest.Close(); err != nil {
		return fmt.Errorf("failed to close destination: %w", err)
	}

	// Atomic rename to final name
	if err := os.Rename(tmpDst, dst); err != nil {
		return fmt.Errorf("failed to rename temporary file: %w", err)
	}

	return nil
}
