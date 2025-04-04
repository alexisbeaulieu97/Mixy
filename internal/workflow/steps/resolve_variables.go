// internal/workflow/steps/resolve_variables.go
package steps

import (
	"errors"
	"log/slog"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

type ResolveVariablesStep struct {
	Resolver core.VariableResolver
}

func (s *ResolveVariablesStep) Name() string { return "resolve_variables" }

func (s *ResolveVariablesStep) Execute(ctx *core.ProjectContext) error {
	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Executing step")

	if s.Resolver == nil {
		panic("ResolveVariablesStep requires a non-nil VariableResolver")
	}
	if ctx.Config == nil {
		return core.NewError(core.ErrorTypeConfiguration, "cannot resolve variables before config is loaded", nil)
	}

	// Pass necessary parts of the context to the resolver
	resolvedVars, err := s.Resolver.Resolve(
		ctx.Config.Variables,          // Defaults from config
		ctx.FlagVariables,             // Overrides from flags (passed in initial context)
		ctx.Config.MandatoryVariables, // Mandatory keys
		ctx,                           // Pass full context for logging, etc.
	)
	if err != nil {
		// Handle cancellation explicitly
		if errors.Is(err, core.ErrCancelled) {
			stepLogger.Warn("Variable resolution cancelled by user.")
			return err // Propagate cancellation signal
		}
		stepLogger.Error("Step failed", slog.Any("error", err))
		return err // Return structured error from resolver
	}

	ctx.Variables = resolvedVars // Store resolved variables in context
	stepLogger.Info("Step completed successfully")
	return nil
}
