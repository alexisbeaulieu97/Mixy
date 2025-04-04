// internal/core/workflow_runner.go
package core

import (
	"errors"
	"fmt"
	"log/slog"
	"os"
)

// WorkflowRunner orchestrates the execution of workflow steps, potentially wrapped by middleware.
type WorkflowRunner struct {
	steps      []WorkflowStep
	middleware []WorkflowMiddleware // Added middleware slice
	logger     *slog.Logger
}

// NewWorkflowRunner creates a runner with the specified steps and middleware.
// Middleware is executed in the order provided (onion-layer style).
func NewWorkflowRunner(steps []WorkflowStep, middleware []WorkflowMiddleware, logger *slog.Logger) *WorkflowRunner {
	if len(steps) == 0 {
		panic("WorkflowRunner requires at least one step")
	}
	if logger == nil {
		panic("WorkflowRunner requires a non-nil logger")
	}
	// Reverse middleware order for easier application in Run loop (innermost first)
	// Or apply in provided order - let's apply as provided for clarity.
	mw := make([]WorkflowMiddleware, len(middleware))
	copy(mw, middleware) // Make a copy

	return &WorkflowRunner{
		steps:      steps,
		middleware: mw, // Store middleware
		logger:     logger.With(slog.String("component", "workflow_runner")),
	}
}

// Run executes the workflow steps sequentially, applying middleware to each step.
func (r *WorkflowRunner) Run(initialCtx ProjectContext) (err error) {
	r.logger.Info("Starting workflow execution",
		slog.Int("total_steps", len(r.steps)),
		slog.Int("middleware_count", len(r.middleware)))

	if initialCtx.Logger == nil {
		initialCtx.Logger = r.logger
	}
	ctx := &initialCtx

	// Defer cleanup (remains the same)
	defer func() {
		if ctx.TempOutputDirectory != "" {
			if err != nil {
				r.logger.Warn("Workflow failed, cleaning up temporary directory",
					slog.String("temp_dir", ctx.TempOutputDirectory),
					slog.Any("triggering_error", err))
				if removeErr := os.RemoveAll(ctx.TempOutputDirectory); removeErr != nil {
					r.logger.Error("Failed to cleanup temporary directory",
						slog.String("temp_dir", ctx.TempOutputDirectory),
						slog.Any("cleanup_error", removeErr))
				} else {
					r.logger.Info("Temporary directory cleaned up successfully.", slog.String("temp_dir", ctx.TempOutputDirectory))
				}
			} else {
				r.logger.Warn("Workflow succeeded but temporary directory path was still set. Cleanup skipped.", slog.String("temp_dir", ctx.TempOutputDirectory))
			}
		}
	}()

	// --- Execute Steps with Middleware ---
	for i, step := range r.steps {
		stepLogger := r.logger.With(slog.Int("step_index", i+1), slog.String("step_name", step.Name()))

		// Define the final action: executing the actual step
		finalHandler := func(execCtx *ProjectContext) error {
			stepLogger.Info("Executing step action") // Log before actual execution
			stepErr := step.Execute(execCtx)
			if stepErr != nil {
				stepLogger.Error("Step action failed", slog.Any("error", stepErr))
			} else {
				stepLogger.Info("Step action completed successfully")
			}
			return stepErr
		}

		// Build the middleware chain for this step, wrapping the finalHandler
		chainedHandler := finalHandler
		// Iterate middleware in reverse to build the onion layers correctly
		// (last middleware in list calls the next-to-last, etc.)
		for j := len(r.middleware) - 1; j >= 0; j-- {
			// Capture loop variables correctly for the closure
			currentMiddleware := r.middleware[j]
			nextHandler := chainedHandler // The handler the current middleware will call

			chainedHandler = func(execCtx *ProjectContext) error {
				middlewareLogger := stepLogger.With(slog.String("middleware", fmt.Sprintf("%T", currentMiddleware)))
				middlewareLogger.Debug("Entering middleware")
				// Execute the current middleware, passing the context, the step being executed,
				// and the *next* handler in the chain (which might be another middleware or the final step execution)
				mwErr := currentMiddleware.Execute(execCtx, step, nextHandler)
				if mwErr != nil {
					middlewareLogger.Debug("Middleware finished with error", slog.Any("error", mwErr))
				} else {
					middlewareLogger.Debug("Middleware finished successfully")
				}
				return mwErr // Return error from middleware execution
			}
		}

		// Execute the fully chained handler (starts with the outermost middleware)
		stepLogger.Info("Starting step execution (via middleware chain)")
		err = chainedHandler(ctx) // Assign result to the named return variable

		// Handle error from the entire chain (middleware or step)
		if err != nil {
			// Logging of specific middleware/step failure happens within the chain/final handler
			if errors.Is(err, ErrCancelled) {
				r.logger.Warn("Workflow execution cancelled by user during step", slog.String("step_name", step.Name()))
			} else {
				r.logger.Error("Workflow execution failed", slog.String("failed_step", step.Name()))
			}
			return err // Stop workflow and trigger deferred cleanup
		}
		stepLogger.Info("Step execution completed successfully (including middleware)")

	} // End step loop

	r.logger.Info("Workflow execution completed successfully")
	return nil // Explicitly return nil on success
}
