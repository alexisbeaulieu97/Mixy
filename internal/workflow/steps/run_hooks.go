// internal/workflow/steps/run_hooks.go
package steps

import (
	"fmt"
	"log/slog"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
	"github.com/alexisbeaulieu97/Mixy/internal/plugin" // Need manager to get hooks
	shared "github.com/alexisbeaulieu97/Mixy/pkg/plugin"
)

type RunHooksStep struct {
	PluginManager *plugin.Manager
}

func (s *RunHooksStep) Name() string { return "run_hooks" }

func (s *RunHooksStep) Execute(ctx *core.ProjectContext) error {
	stepLogger := ctx.Logger.With(slog.String("step", s.Name()))
	stepLogger.Info("Executing step")

	if s.PluginManager == nil {
		panic("RunHooksStep requires a non-nil PluginManager")
	}
	if ctx.Config == nil || ctx.Variables == nil || ctx.OutputDirectory == "" {
		return core.NewError(core.ErrorTypeUnknown, "cannot run hooks before core workflow steps are complete", nil)
	}

	if len(ctx.Config.Hooks) == 0 {
		stepLogger.Debug("No post-processing hooks configured.")
		return nil // Nothing to do
	}

	stepLogger.Info("Executing post-processing hooks", slog.Any("hooks", ctx.Config.Hooks))
	hookCtx := shared.HookPluginContext{
		Variables:       ctx.Variables,
		OutputDirectory: ctx.OutputDirectory,
	}

	for _, hookName := range ctx.Config.Hooks {
		hookLogger := stepLogger.With(slog.String("hook_name", hookName))
		hookLogger.Info("Executing hook")
		hookPlugin, ok := s.PluginManager.GetHook(hookName)
		if !ok {
			hookLogger.Error("Configured post-processing hook not found or loaded")
			return core.NewPluginError(fmt.Sprintf("configured hook '%s' not found", hookName), nil)
		}

		meta, _ := hookPlugin.GetMetadata()
		hookLogger = hookLogger.With(slog.String("plugin_name", meta.Name), slog.String("plugin_version", meta.PluginVersion))
		hookType := "PostGenerate"
		hookLogger.Debug("Calling hook plugin Execute", slog.String("hook_type", hookType))

		err := hookPlugin.Execute(hookType, hookCtx)
		if err != nil {
			hookLogger.Error("Hook execution failed", slog.Any("error", err))
			return core.NewPluginError(fmt.Sprintf("hook '%s' (Plugin: %s) failed", hookName, meta.Name), err)
		}
		hookLogger.Info("Hook executed successfully")
	}

	stepLogger.Info("Step completed successfully")
	return nil
}
