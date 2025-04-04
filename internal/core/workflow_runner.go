// internal/core/workflow_runner.go
package core

import (
	"errors"
	"fmt"
	"log/slog"
	"os"
)

// Package core provides core workflow execution functionality.

// WorkflowRunner orchestrates the execution of workflow steps with middleware support.
// It ensures proper cleanup of temporary resources and provides detailed logging of the execution process.
type WorkflowRunner struct {
	steps      []WorkflowStep
	middleware []WorkflowMiddleware
	logger     *slog.Logger
}

// NewWorkflowRunner creates a new workflow runner instance.
// It requires at least one step and a logger to be provided.
//
// Parameters:
//   - steps: The ordered sequence of workflow steps to execute
//   - middleware: Optional middleware to wrap step execution (can be nil)
//   - logger: Required logger for execution tracking
//
// Returns:
//   - *WorkflowRunner: Configured workflow runner instance
//
// Panics if steps is empty or logger is nil as these are required for proper operation.
func NewWorkflowRunner(steps []WorkflowStep, middleware []WorkflowMiddleware, logger *slog.Logger) *WorkflowRunner {
	if len(steps) == 0 {
		panic("workflow runner requires at least one step")
	}
	if logger == nil {
		panic("workflow runner requires a non-nil logger")
	}

	// Create a defensive copy of middleware slice
	var mw []WorkflowMiddleware
	if middleware != nil {
		mw = make([]WorkflowMiddleware, len(middleware))
		copy(mw, middleware)
	}

	return &WorkflowRunner{
		steps:      steps,
		middleware: mw,
		logger:     logger.With(slog.String("component", "workflow_runner")),
	}
}

// cleanupTempDir handles the cleanup of temporary directories, with proper logging.
func (r *WorkflowRunner) cleanupTempDir(ctx *ProjectContext, workflowErr error) {
	if ctx.TempOutputDirectory == "" {
		return
	}

	logger := r.logger.With(slog.String("temp_dir", ctx.TempOutputDirectory))

	// Only clean up on error to preserve output for debugging
	if workflowErr != nil {
		logger.Warn("Workflow failed, cleaning up temporary directory",
			slog.Any("triggering_error", workflowErr))

		if removeErr := os.RemoveAll(ctx.TempOutputDirectory); removeErr != nil {
			logger.Error("Failed to cleanup temporary directory",
				slog.Any("cleanup_error", removeErr))
		} else {
			logger.Info("Temporary directory cleaned up successfully")
		}
		return
	}

	// Warn about lingering temp directories
	logger.Warn("Workflow succeeded but temporary directory path was still set (potential leak)")
}

// Run executes the workflow steps sequentially, applying middleware to each step.
// It ensures proper initialization of the context and handles cleanup of temporary resources.
//
// Parameters:
//   - initialCtx: The initial project context for the workflow
//
// Returns:
//   - error: nil if successful, otherwise the error that caused the workflow to fail
func (r *WorkflowRunner) Run(initialCtx ProjectContext) (err error) {
	r.logger.Info("Starting workflow execution",
		slog.Int("total_steps", len(r.steps)),
		slog.Int("middleware_count", len(r.middleware)))

	// Ensure context has a logger
	if initialCtx.Logger == nil {
		initialCtx.Logger = r.logger.With(slog.String("context", "workflow"))
	}
	ctx := &initialCtx

	// Register cleanup handler
	defer func() {
		r.cleanupTempDir(ctx, err)
	}()

	// Handle panics
	defer func() {
		if panicVal := recover(); panicVal != nil {
			err = fmt.Errorf("workflow panic: %v", panicVal)
			r.logger.Error("Workflow execution panic",
				slog.Any("panic_value", panicVal))
		}
	}()

	// Execute each step in sequence
	for i, step := range r.steps {
		stepLogger := r.logger.With(
			slog.Int("step_index", i+1),
			slog.String("step_name", step.Name()))

		// Create the base handler that executes the step
		finalHandler := func(execCtx *ProjectContext) error {
			stepLogger.Info("Executing step action")
			if err := step.Execute(execCtx); err != nil {
				stepLogger.Error("Step action failed",
					slog.Any("error", err))
				return fmt.Errorf("step %s failed: %w", step.Name(), err)
			}
			stepLogger.Info("Step action completed successfully")
			return nil
		}

		// Build the middleware chain
		chainedHandler := finalHandler
		for j := len(r.middleware) - 1; j >= 0; j-- {
			currentMiddleware := r.middleware[j]
			nextHandler := chainedHandler

			chainedHandler = func(execCtx *ProjectContext) error {
				middlewareLogger := stepLogger.With(
					slog.String("middleware", fmt.Sprintf("%T", currentMiddleware)))

				middlewareLogger.Debug("Entering middleware")
				if err := currentMiddleware.Execute(execCtx, step, nextHandler); err != nil {
					middlewareLogger.Error("Middleware failed",
						slog.Any("error", err))
					return fmt.Errorf("middleware failed for step %s: %w", step.Name(), err)
				}
				middlewareLogger.Debug("Middleware completed successfully")
				return nil
			}
		}

		// Execute the step with its middleware chain
		stepLogger.Info("Starting step execution (via middleware chain)")
		if err = chainedHandler(ctx); err != nil {
			if errors.Is(err, ErrCancelled) {
				r.logger.Warn("Workflow execution cancelled by user",
					slog.String("step", step.Name()))
				return fmt.Errorf("workflow cancelled: %w", err)
			}
			r.logger.Error("Workflow execution failed",
				slog.String("step", step.Name()))
			return fmt.Errorf("workflow failed at step %s: %w", step.Name(), err)
		}
		stepLogger.Info("Step execution completed successfully")
	}

	r.logger.Info("Workflow execution completed successfully")
	return nil
}
