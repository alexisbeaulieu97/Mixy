// internal/loader/plugin_loader_adapter.go
package loader

import (
	"fmt"
	"log"
	"strings" // Import strings

	// Use your actual project paths
	"github.com/alexisbeaulieu97/Mixy/internal/core"
	"github.com/alexisbeaulieu97/Mixy/internal/plugin"
	shared "github.com/alexisbeaulieu97/Mixy/pkg/plugin"
)

// PluginLoaderAdapter uses the PluginManager to load templates via plugins.
type PluginLoaderAdapter struct {
	manager *plugin.Manager // Reference to the plugin manager
}

// NewPluginLoaderAdapter creates a new adapter.
func NewPluginLoaderAdapter(manager *plugin.Manager) core.TemplateLoader {
	return &PluginLoaderAdapter{manager: manager}
}

// Supports checks if the source uses the "plugin:<name>..." format AND
// if the corresponding plugin exists in the manager.
func (a *PluginLoaderAdapter) Supports(source string) bool {
	// Check 1: Does it look like a plugin source string?
	if !strings.HasPrefix(source, "plugin:") {
		return false
	}

	// Check 2: Can we parse a name?
	parts := strings.SplitN(source, ":", 3)
	if len(parts) < 2 {
		log.Printf("PluginLoaderAdapter: Invalid plugin source format '%s'. Skipping.\n", source)
		return false // Malformed
	}
	pluginName := parts[1]
	if pluginName == "" {
		log.Printf("PluginLoaderAdapter: Empty plugin name in source '%s'. Skipping.\n", source)
		return false // Empty name
	}

	// Check 3: Does the plugin manager have a loader with this name?
	loaderPlugin, ok := a.manager.GetLoaderPluginByName(pluginName) // Use helper method
	if !ok || loaderPlugin == nil {
		// This is expected if a plugin isn't installed, so don't log verbosely unless debugging
		// log.Printf("PluginLoaderAdapter: No registered plugin loader found for name '%s' in source '%s'.\n", pluginName, source)
		return false
	}

	// If all checks pass, this adapter supports this source string.
	// log.Printf("PluginLoaderAdapter: Supports source '%s' via plugin '%s'.\n", source, pluginName) // Can be verbose
	return true
}

// Load retrieves the plugin instance via the manager and calls its Load method.
func (a *PluginLoaderAdapter) Load(source string, ctx *core.ProjectContext) (core.Template, error) {
	// Parse the source string ("plugin:<name>:<plugin-specific-data>")
	// Supports() should have already validated the basic format.
	parts := strings.SplitN(source, ":", 3)
	if len(parts) < 2 { // Should not happen if Supports() worked correctly
		return nil, fmt.Errorf("internal error: invalid plugin source format '%s' passed to PluginLoaderAdapter.Load", source)
	}
	pluginName := parts[1]
	pluginSpecificSource := ""
	if len(parts) == 3 {
		pluginSpecificSource = parts[2]
	}

	// Get the specific plugin *instance* from the manager
	loaderPlugin, ok := a.manager.GetLoaderPluginByName(pluginName)
	if !ok || loaderPlugin == nil {
		// This indicates an internal inconsistency if Supports() passed but the plugin disappeared
		return nil, fmt.Errorf("internal error: plugin loader '%s' not found by manager in Load (source: %s)", pluginName, source)
	}

	// Get metadata for logging (best effort)
	meta, errMeta := loaderPlugin.GetMetadata()
	pluginLogName := pluginName // Fallback to registered name
	if errMeta == nil {
		pluginLogName = meta.Name // Prefer plugin's self-reported name
	}
	log.Printf("PluginLoaderAdapter: Using loader plugin '%s' for source '%s' (plugin-specific part: '%s')\n", pluginLogName, source, pluginSpecificSource)

	// Prepare context for the plugin
	pluginCtx := shared.LoaderPluginContext{
		Variables: ctx.Variables,
	}

	// Call the actual plugin's Load method via RPC
	pluginData, err := loaderPlugin.Load(pluginSpecificSource, pluginCtx)
	if err != nil {
		// Report error using the plugin's name and the data *it* received
		return nil, fmt.Errorf("plugin '%s' failed to load source '%s': %w", pluginLogName, pluginSpecificSource, err)
	}

	// Adapt the returned data
	coreData := make([]core.TemplateData, len(pluginData))
	for i, pd := range pluginData {
		coreData[i] = core.NewInMemoryTemplateData(pd.Path, pd.Content)
	}

	// Return a core.Template representing the loaded data
	return &LoadedPluginTemplate{
		SourceName: source, // Use the original full source string as the identifier
		LoadedData: coreData,
	}, nil
}

// LoadedPluginTemplate is a simple implementation of core.Template for data loaded by a plugin.
type LoadedPluginTemplate struct {
	SourceName string
	LoadedData []core.TemplateData
}

func (lpt *LoadedPluginTemplate) Source() string {
	return lpt.SourceName
}

// Load just returns the data already loaded by the plugin adapter.
func (lpt *LoadedPluginTemplate) Load(ctx *core.ProjectContext) ([]core.TemplateData, error) {
	// Note: Variables are typically applied during rendering, not here.
	// If plugins *can* pre-render, the interface might need adjustment.
	return lpt.LoadedData, nil
}

// --- Ensure you have this method in PluginManager ---
// Add the following GetLoaderPluginByName method to internal/plugin/manager.go if it doesn't exist:

/* Add to internal/plugin/manager.go:
// GetLoaderPluginByName retrieves a loaded loader plugin interface by its registered name.
func (m *Manager) GetLoaderPluginByName(name string) (shared.LoaderInterface, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	// Optional: Check m.isLoaded if strict ordering is needed
	loader, ok := m.loaderPlugins[name]
	return loader, ok
}
*/
