// internal/workflow/steps/finalize_output.go
package steps

import (
	"fmt"
	"io" // Need io package
	"io/fs"
	"log/slog"
	"os"
	"path/filepath" // Need path/filepath

	"github.com/alexisbeaulieu97/Mixy/internal/core" // Use correct path
)

type FinalizeOutputStep struct{}

func (s *FinalizeOutputStep) Name() string { return "finalize_output" }

func (s *FinalizeOutputStep) Execute(ctx *core.ProjectContext) error {
	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Executing step")

	if ctx.TempOutputDirectory == "" {
		return core.NewError(core.ErrorTypeUnknown, "temporary output directory path is missing", nil)
	}
	if ctx.OutputDirectory == "" {
		return core.NewError(core.ErrorTypeConfiguration, "final output directory path is missing", nil)
	}

	tempDir := ctx.TempOutputDirectory
	finalDir := ctx.OutputDirectory
	stepLogger = stepLogger.With(
		slog.String("temp_dir", tempDir),
		slog.String("final_dir", finalDir),
	)

	stepLogger.Info("Attempting to copy temporary output to final destination")

	// --- Prepare Destination ---
	// Check if the final destination exists. Overwrite strategy.
	if _, err := os.Stat(finalDir); err == nil {
		stepLogger.Warn("Final output directory already exists, removing it before copying temp output.", slog.String("path", finalDir))
		if err := os.RemoveAll(finalDir); err != nil {
			stepLogger.Error("Failed to remove existing final output directory", slog.Any("error", err))
			// Don't remove tempDir here, user might want it.
			return core.NewIOError("failed to remove existing output directory", err, slog.String("path", finalDir))
		}
		stepLogger.Info("Existing final output directory removed.")
	} else if !os.IsNotExist(err) {
		// Error stating the final directory other than not existing
		stepLogger.Error("Failed to check status of final output directory", slog.Any("error", err))
		return core.NewIOError("failed to check status of final output directory", err, slog.String("path", finalDir))
	}

	// Ensure the parent directory of the final destination exists before copying
	finalDirParent := filepath.Dir(finalDir)
	if err := os.MkdirAll(finalDirParent, 0755); err != nil {
		stepLogger.Error("Failed to create parent directory for final destination", slog.String("parent_dir", finalDirParent), slog.Any("error", err))
		return core.NewIOError("failed to create parent directory for final output", err, slog.String("path", finalDirParent))
	}

	// --- Perform Copy ---
	stepLogger.Debug("Starting recursive copy from temp to final directory")
	if err := copyDirectory(tempDir, finalDir, stepLogger); err != nil {
		stepLogger.Error("Failed to copy temporary directory contents to final destination", slog.Any("error", err))
		// Don't remove tempDir, user might want to inspect it on copy failure
		return core.NewIOError("failed to copy temporary directory", err, slog.String("from", tempDir), slog.String("to", finalDir))
	}
	stepLogger.Info("Successfully copied temporary directory contents")

	// --- Cleanup Temp Dir (after successful copy) ---
	stepLogger.Debug("Removing temporary directory after successful copy")
	if err := os.RemoveAll(tempDir); err != nil {
		// Log error but don't fail the whole step, copy was successful.
		stepLogger.Error("Failed to remove temporary directory after copy, manual cleanup might be needed", slog.Any("error", err))
	} else {
		stepLogger.Debug("Temporary directory removed successfully")
	}

	// Prevent cleanup by the runner defer func
	ctx.TempOutputDirectory = ""

	stepLogger.Info("Step completed successfully, output finalized.")
	return nil
}

// copyDirectory recursively copies files and directories from src to dst.
// It preserves file modes.
func copyDirectory(src, dst string, logger *slog.Logger) error {
	return filepath.WalkDir(src, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			logger.Error("Error accessing path during copy walk", slog.String("path", path), slog.Any("error", err))
			return err // Propagate the error from WalkDir
		}

		// Calculate the relative path from the source base
		relPath, err := filepath.Rel(src, path)
		if err != nil {
			// Should not happen if path is within src
			logger.Error("Failed to calculate relative path during copy", slog.String("src", src), slog.String("path", path), slog.Any("error", err))
			return fmt.Errorf("calculating relative path for %s: %w", path, err)
		}

		// Construct the destination path
		dstPath := filepath.Join(dst, relPath)
		copyLogger := logger.With(slog.String("src_path", path), slog.String("dst_path", dstPath))

		if d.IsDir() {
			// Create the destination directory with the same permissions as the source
			srcInfo, statErr := d.Info() // Get FileInfo for mode
			if statErr != nil {
				copyLogger.Error("Failed to get source directory info for mode", slog.Any("error", statErr))
				return fmt.Errorf("getting source dir info for %s: %w", path, statErr)
			}
			copyLogger.Debug("Creating destination directory", slog.Any("mode", srcInfo.Mode()))
			if err := os.MkdirAll(dstPath, srcInfo.Mode()); err != nil {
				copyLogger.Error("Failed to create destination directory", slog.Any("error", err))
				return fmt.Errorf("creating destination directory %s: %w", dstPath, err)
			}
		} else { // It's a file
			// Copy the file content and mode
			if err := copyFile(path, dstPath, d, copyLogger); err != nil {
				// copyFile logs details
				return fmt.Errorf("copying file from %s to %s: %w", path, dstPath, err)
			}
		}
		return nil // Continue walking
	})
}

// copyFile copies a single file from src to dst, preserving mode.
func copyFile(srcFile, dstFile string, srcEntry fs.DirEntry, logger *slog.Logger) error {
	srcInfo, err := srcEntry.Info()
	if err != nil {
		logger.Error("Failed to get source file info", slog.Any("error", err))
		return fmt.Errorf("getting source file info for %s: %w", srcFile, err)
	}
	mode := srcInfo.Mode()

	source, err := os.Open(srcFile)
	if err != nil {
		logger.Error("Failed to open source file", slog.Any("error", err))
		return fmt.Errorf("opening source file %s: %w", srcFile, err)
	}
	defer source.Close()

	// Create destination file with the source file's permissions
	logger.Debug("Creating destination file", slog.Any("mode", mode))
	destination, err := os.OpenFile(dstFile, os.O_RDWR|os.O_CREATE|os.O_TRUNC, mode)
	if err != nil {
		logger.Error("Failed to create destination file", slog.Any("error", err))
		return fmt.Errorf("creating destination file %s: %w", dstFile, err)
	}
	defer destination.Close()

	// Copy content
	logger.Debug("Copying file content")
	bytesCopied, err := io.Copy(destination, source)
	if err != nil {
		logger.Error("Failed to copy file content", slog.Any("error", err))
		return fmt.Errorf("copying content from %s to %s: %w", srcFile, dstFile, err)
	}
	logger.Debug("File content copied successfully", slog.Int64("bytes", bytesCopied))

	// Ensure destination file has correct mode (OpenFile might be affected by umask)
	err = os.Chmod(dstFile, mode)
	if err != nil {
		logger.Warn("Failed to set final permissions on destination file", slog.Any("error", err))
		// Log warning but don't fail the whole copy for a chmod error usually
	}

	return nil
}
