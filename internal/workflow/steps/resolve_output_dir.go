// Package steps provides workflow step implementations for Mixy's template processing pipeline.
package steps

import (
	"fmt"
	"log/slog"
	"os"
	"path/filepath"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// ResolveOutputDirStep determines and validates the final output directory
// for generated project files. It considers configuration settings, command-line
// flags, and validates the chosen location is suitable for output.
type ResolveOutputDirStep struct {
	// Options configures output directory resolution behavior
	Options OutputDirOptions
}

// OutputDirOptions configures how the output directory is resolved and validated.
type OutputDirOptions struct {
	// DefaultDir specifies the default output directory when none is provided
	// If empty, "." (current directory) is used
	DefaultDir string

	// RequireEmpty indicates whether the output directory must be empty
	RequireEmpty bool

	// CreateIfMissing indicates whether to create the directory if it doesn't exist
	CreateIfMissing bool

	// AllowParentCreation indicates whether to create parent directories
	AllowParentCreation bool
}

// NewResolveOutputDirStep creates a new step with the given options.
//
// Parameters:
//   - options: Optional configuration for output directory resolution
//
// Returns:
//   - *ResolveOutputDirStep: The configured step
func NewResolveOutputDirStep(options OutputDirOptions) *ResolveOutputDirStep {
	// Set default directory if not specified
	if options.DefaultDir == "" {
		options.DefaultDir = "."
	}

	return &ResolveOutputDirStep{
		Options: options,
	}
}

// Name returns the step's identifier.
func (s *ResolveOutputDirStep) Name() string {
	return "resolve_output_dir"
}

// Execute determines and validates the output directory location.
func (s *ResolveOutputDirStep) Execute(ctx *core.ProjectContext) error {
	if ctx == nil {
		return core.NewIOError("nil context provided", nil)
	}
	if ctx.Logger == nil {
		return core.NewIOError("nil logger in context", nil)
	}

	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))

	// Validate config after logger is available for better error reporting
	if ctx.Config == nil {
		stepLogger.Error("Missing required configuration")
		return core.NewConfigurationError("configuration is required for output directory resolution", nil)
	}
	stepLogger.Info("Resolving output directory")

	// Determine output directory
	outputDir := s.resolveOutputPath(ctx, stepLogger)

	// Convert to absolute path
	absOutputDir, err := filepath.Abs(outputDir)
	if err != nil {
		stepLogger.Error("Failed to determine absolute path",
			slog.String("path", outputDir),
			slog.Any("error", err))
		return core.NewIOError(
			fmt.Sprintf("failed to resolve absolute path for '%s'", outputDir),
			err)
	}

	// Validate and potentially create directory
	if err := s.validateOutputDir(absOutputDir, stepLogger); err != nil {
		return err
	}

	// Store result
	ctx.OutputDirectory = absOutputDir

	stepLogger.Info("Output directory resolved successfully",
		slog.String("path", absOutputDir))

	return nil
}

// resolveOutputPath determines the output directory path from available sources.
func (s *ResolveOutputDirStep) resolveOutputPath(ctx *core.ProjectContext, logger *slog.Logger) string {
	// Start with default
	outputDir := s.Options.DefaultDir

	// Use config value if available
	if ctx.Config.Output != "" {
		outputDir = ctx.Config.Output
		logger.Debug("Using output directory from config",
			slog.String("dir", outputDir))
	}

	// Allow flag override
	if ctx.OutputDirectory != "" {
		outputDir = ctx.OutputDirectory
		logger.Info("Using output directory from flag",
			slog.String("dir", outputDir))
	}

	return outputDir
}

// validateOutputDir ensures the output directory is valid and available.
func (s *ResolveOutputDirStep) validateOutputDir(dir string, logger *slog.Logger) error {
	// Check existence
	info, err := os.Stat(dir)
	if err != nil {
		if os.IsNotExist(err) {
			if !s.Options.CreateIfMissing {
				return core.NewIOError(
					fmt.Sprintf("output directory does not exist: %s", dir),
					err)
			}

			// Create directory (and parents if allowed)
			createErr := s.createOutputDir(dir, logger)
			if createErr != nil {
				return createErr
			}

			logger.Info("Created output directory",
				slog.String("dir", dir))
			return nil
		}

		return core.NewIOError(
			fmt.Sprintf("failed to check output directory: %s", dir),
			err)
	}

	// Ensure it's a directory
	if !info.IsDir() {
		return core.NewIOError(
			fmt.Sprintf("output path exists but is not a directory: %s", dir),
			nil)
	}

	// Check if empty when required
	if s.Options.RequireEmpty {
		empty, err := s.isDirEmpty(dir)
		if err != nil {
			return core.NewIOError(
				fmt.Sprintf("failed to check if directory is empty: %s", dir),
				err)
		}
		if !empty {
			return core.NewIOError(
				fmt.Sprintf("output directory is not empty: %s", dir),
				nil)
		}
	}

	return nil
}

// createOutputDir attempts to create the output directory.
func (s *ResolveOutputDirStep) createOutputDir(dir string, logger *slog.Logger) error {
	var err error
	if s.Options.AllowParentCreation {
		err = os.MkdirAll(dir, 0755)
	} else {
		err = os.Mkdir(dir, 0755)
	}

	if err != nil {
		logger.Error("Failed to create output directory",
			slog.String("dir", dir),
			slog.Any("error", err))
		return core.NewIOError(
			fmt.Sprintf("failed to create output directory: %s", dir),
			err)
	}

	return nil
}

// isDirEmpty checks if a directory contains any files or subdirectories.
func (s *ResolveOutputDirStep) isDirEmpty(dir string) (bool, error) {
	f, err := os.Open(dir)
	if err != nil {
		return false, fmt.Errorf("failed to open directory: %w", err)
	}
	defer f.Close()

	// Try to read one entry
	entries, err := f.ReadDir(1)
	if err != nil {
		if os.IsNotExist(err) {
			return false, fmt.Errorf("directory does not exist: %w", err)
		}
	}

	// No error means we found at least one entry
	if err == nil && len(entries) > 0 {
		return false, nil
	}

	// io.EOF error means directory is empty
	return true, nil
}
