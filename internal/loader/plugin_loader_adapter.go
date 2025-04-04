// internal/loader/plugin_loader_adapter.go
package loader

import (
	"errors"
	"fmt"
	"io/fs"    // Import fs
	"log/slog" // Use slog

	// Import strings
	"github.com/alexisbeaulieu97/Mixy/internal/core"
	"github.com/alexisbeaulieu97/Mixy/internal/plugin"   // Host-side manager
	shared "github.com/alexisbeaulieu97/Mixy/pkg/plugin" // Shared types
)

// PluginLoaderAdapter uses the PluginManager to load templates via plugins.
type PluginLoaderAdapter struct {
	manager *plugin.Manager
	logger  *slog.Logger
}

// NewPluginLoaderAdapter creates a new adapter.
func NewPluginLoaderAdapter(manager *plugin.Manager, logger *slog.Logger) core.TemplateLoader {
	return &PluginLoaderAdapter{
		manager: manager,
		logger:  logger.With(slog.String("component", "plugin_loader_adapter")),
	}
}

// Supports checks if the PluginManager has a loader that claims the source.
// Source format expected: "plugin:<name>:<details>"
func (a *PluginLoaderAdapter) Supports(source string) bool {
	// The manager's GetLoader now handles the prefix check
	loader, _, ok := a.manager.GetLoader(source)
	supported := ok && loader != nil
	a.logger.Debug("Checking plugin support for source", slog.String("source", source), slog.Bool("supported", supported))
	return supported
}

// Load retrieves the plugin instance via the manager and calls its Load method.
func (a *PluginLoaderAdapter) Load(source string, ctx *core.ProjectContext) (core.Template, error) {
	logger := ctx.Logger.With(slog.String("component", "plugin_loader_adapter"), slog.String("source", source)) // Use ctx logger
	logger.Debug("Attempting to load template via plugin")

	loaderPlugin, pluginSpecificSource, ok := a.manager.GetLoader(source)
	if !ok || loaderPlugin == nil {
		err := errors.New("no suitable plugin loader found")
		logger.Error("Plugin loader not found or manager not ready", slog.Any("error", err))
		return nil, core.NewPluginError("no suitable plugin loader found", err, slog.String("source", source))
	}

	// Get metadata for logging purposes
	meta, metaErr := loaderPlugin.GetMetadata()
	if metaErr != nil {
		// Log warning but proceed if possible, using a placeholder name
		logger.Warn("Failed to get metadata from plugin", slog.Any("error", metaErr))
		meta.Name = "[unknown plugin]"
	}
	pluginLogger := logger.With(slog.String("plugin_name", meta.Name), slog.String("plugin_version", meta.PluginVersion), slog.String("plugin_api_version", meta.APIVersion))
	pluginLogger.Info("Using plugin loader")

	// Prepare context for the plugin (simple version)
	pluginCtx := shared.LoaderPluginContext{
		Variables: ctx.Variables,
		// Add other necessary fields here if the shared context evolves
	}
	pluginLogger.Debug("Calling plugin Load method", slog.String("plugin_specific_source", pluginSpecificSource), slog.Any("context_variables", pluginCtx.Variables))

	// Call the plugin's Load method
	pluginData, err := loaderPlugin.Load(pluginSpecificSource, pluginCtx)
	if err != nil {
		pluginLogger.Error("Plugin failed to load source", slog.Any("error", err))
		// Wrap error with plugin context
		return nil, core.NewPluginError(fmt.Sprintf("plugin '%s' failed to load source", meta.Name), err, slog.String("plugin_name", meta.Name), slog.String("plugin_source_details", pluginSpecificSource))
	}
	pluginLogger.Info("Plugin loaded source data successfully", slog.Int("file_count", len(pluginData)))

	// Adapt the plugin's returned data to core.TemplateData
	coreData := make([]core.TemplateData, len(pluginData))
	for i, pd := range pluginData {
		fileLogger := pluginLogger.With(slog.String("relative_path", pd.Path))
		fileLogger.Debug("Adapting plugin data to core data", slog.Int("content_size", len(pd.Content)), slog.Uint64("mode", uint64(pd.Mode)))
		// Convert mode back from uint32
		mode := fs.FileMode(pd.Mode)
		coreData[i] = core.NewInMemoryTemplateData(pd.Path, pd.Content, mode)
	}

	// Wrap the result in a core.Template compatible structure
	return &LoadedPluginTemplate{
		SourceName: source, // The original source string (e.g., "plugin:name:details")
		LoadedData: coreData,
		Logger:     logger,
	}, nil
}

// LoadedPluginTemplate is a simple implementation of core.Template for data loaded by a plugin.
type LoadedPluginTemplate struct {
	SourceName string
	LoadedData []core.TemplateData
	Logger     *slog.Logger
}

func (lpt *LoadedPluginTemplate) Source() string {
	return lpt.SourceName
}

// Load just returns the data already loaded by the plugin adapter.
func (lpt *LoadedPluginTemplate) Load(ctx *core.ProjectContext) ([]core.TemplateData, error) {
	lpt.Logger.Debug("Providing pre-loaded data from plugin", slog.String("source", lpt.SourceName), slog.Int("file_count", len(lpt.LoadedData)))
	return lpt.LoadedData, nil
}
