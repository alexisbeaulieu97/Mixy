// Package steps provides workflow step implementations for Mixy's template processing pipeline.
package steps

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
	"github.com/alexisbeaulieu97/Mixy/internal/plugin"
	shared "github.com/alexisbeaulieu97/Mixy/pkg/plugin"
)

// RunHooksStep executes configured post-processing hooks after template generation.
// It manages hook execution, timeouts, and error handling.
type RunHooksStep struct {
	// PluginManager provides access to loaded hook plugins
	PluginManager *plugin.Manager

	// Options configures hook execution behavior
	Options HookOptions
}

// HookOptions configures how hooks are executed.
type HookOptions struct {
	// Timeout is the maximum duration to wait for a hook to complete
	// Default: 5 minutes
	Timeout time.Duration

	// ContinueOnError indicates whether to continue executing
	// remaining hooks if one fails
	ContinueOnError bool

	// SkipMissing indicates whether to ignore hooks that
	// aren't found instead of failing
	SkipMissing bool

	// Environment provides additional environment variables
	// to pass to hook executions
	Environment map[string]string
}

// defaultHookTimeout is used when no timeout is specified
const defaultHookTimeout = 5 * time.Minute

// NewRunHooksStep creates a new step with the given plugin manager and options.
//
// Parameters:
//   - manager: The plugin manager for accessing hook plugins
//   - options: Optional configuration for hook execution
//
// Returns:
//   - *RunHooksStep: The configured step
//
// Panics if manager is nil, as it's required for operation.
func NewRunHooksStep(manager *plugin.Manager, options HookOptions) *RunHooksStep {
	if manager == nil {
		panic("plugin manager is required")
	}

	// Set default timeout if not specified
	if options.Timeout == 0 {
		options.Timeout = defaultHookTimeout
	}

	return &RunHooksStep{
		PluginManager: manager,
		Options:       options,
	}
}

// Name returns the step's identifier.
func (s *RunHooksStep) Name() string {
	return "run_hooks"
}

// Execute runs all configured post-processing hooks.
func (s *RunHooksStep) Execute(ctx *core.ProjectContext) error {
	// Input validation
	if ctx == nil {
		return core.NewPluginError("nil context provided", nil)
	}
	if ctx.Logger == nil {
		return core.NewPluginError("nil logger in context", nil)
	}
	if ctx.Config == nil {
		return core.NewPluginError("nil configuration in context", nil)
	}
	if ctx.Variables == nil {
		return core.NewPluginError("nil variables in context", nil)
	}
	if ctx.OutputDirectory == "" {
		return core.NewPluginError("output directory not set", nil)
	}

	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))

	// Check for hooks to run
	if len(ctx.Config.Hooks) == 0 {
		stepLogger.Debug("No post-processing hooks configured")
		return nil
	}

	stepLogger.Info("Running post-processing hooks",
		slog.Int("hook_count", len(ctx.Config.Hooks)))

	// Create hook execution context with timeouts
	hookCtx := s.createHookContext(ctx, stepLogger)

	// Run each hook
	var lastError error
	for i, hookName := range ctx.Config.Hooks {
		if err := s.runHook(hookName, hookCtx, stepLogger); err != nil {
			if !s.Options.ContinueOnError {
				return fmt.Errorf("hook execution failed: %w", err)
			}
			lastError = err
			stepLogger.Error("Hook failed but continuing",
				slog.String("hook", hookName),
				slog.Int("hook_index", i+1),
				slog.Any("error", err))
		}
	}

	if lastError != nil {
		return core.NewPluginError("one or more hooks failed", lastError)
	}

	stepLogger.Info("All hooks completed successfully")
	return nil
}

// createHookContext prepares the hook execution context with variables.
func (s *RunHooksStep) createHookContext(ctx *core.ProjectContext, logger *slog.Logger) shared.HookPluginContext {
	hookCtx := shared.HookPluginContext{
		Variables:       make(map[string]interface{}),
		OutputDirectory: ctx.OutputDirectory,
	}

	// Copy variables to prevent hooks from modifying the original
	for k, v := range ctx.Variables {
		hookCtx.Variables[k] = v
	}

	// Handle environment variables if needed
	// Note: environment variables must be handled by the hook plugin itself
	// through its Execute method as HookPluginContext doesn't define Environment
	if len(s.Options.Environment) > 0 {
		logger.Debug("Environment variables available for hook",
			slog.Int("env_var_count", len(s.Options.Environment)))
	}

	return hookCtx
}

// runHook executes a single hook with timeout and error handling.
func (s *RunHooksStep) runHook(hookName string, hookCtx shared.HookPluginContext, logger *slog.Logger) error {
	hookLogger := logger.With(slog.String("hook", hookName))
	hookLogger.Info("Starting hook execution")

	// Get the hook plugin
	hookPlugin, ok := s.PluginManager.GetHook(hookName)
	if !ok {
		if s.Options.SkipMissing {
			hookLogger.Warn("Hook plugin not found, skipping")
			return nil
		}
		return core.NewPluginError(
			fmt.Sprintf("hook plugin not found: %s", hookName),
			nil)
	}

	// Get metadata for logging
	meta, _ := hookPlugin.GetMetadata()
	hookLogger = hookLogger.With(
		slog.String("plugin_name", meta.Name),
		slog.String("plugin_version", meta.PluginVersion))

	// Create context with timeout
	timeoutCtx, cancel := context.WithTimeout(context.Background(), s.Options.Timeout)
	defer cancel()

	// Execute hook with timeout
	done := make(chan error, 1)
	go func() {
		done <- hookPlugin.Execute("PostGenerate", hookCtx)
	}()

	// Wait for completion or timeout
	select {
	case err := <-done:
		if err != nil {
			hookLogger.Error("Hook execution failed",
				slog.Any("error", err))
			return core.NewPluginError(
				fmt.Sprintf("hook execution failed: %s", hookName),
				err)
		}
		hookLogger.Info("Hook execution completed successfully")
		return nil

	case <-timeoutCtx.Done():
		hookLogger.Error("Hook execution timed out",
			slog.Duration("timeout", s.Options.Timeout))
		return core.NewPluginError(
			fmt.Sprintf("hook timed out after %v: %s", s.Options.Timeout, hookName),
			timeoutCtx.Err())
	}
}
