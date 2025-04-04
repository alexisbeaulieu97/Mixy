// internal/plugin/manager.go
package plugin

import (
	"fmt"
	"log" // Keep standard log for manager's own messages if desired
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"

	shared "github.com/alexisbeaulieu97/Mixy/pkg/plugin"
	"github.com/hashicorp/go-hclog" // Import hclog
	"github.com/hashicorp/go-plugin"
)

// Manager handles discovery and management of Mixy plugins.
type Manager struct {
	pluginDir     string                            // Directory to scan for plugins (optional)
	clients       map[string]*plugin.Client         // Map plugin executable path to client
	loaderPlugins map[string]shared.LoaderInterface // Map plugin name to loader interface
	hookPlugins   map[string]shared.HookInterface   // Map plugin name to hook interface
	mu            sync.RWMutex
	isLoaded      bool
}

// NewManager creates a new plugin manager.
// pluginDir: Optional directory to explicitly scan for plugins. If empty, scans PATH.
func NewManager(pluginDir string) *Manager {
	return &Manager{
		pluginDir:     pluginDir,
		clients:       make(map[string]*plugin.Client),
		loaderPlugins: make(map[string]shared.LoaderInterface),
		hookPlugins:   make(map[string]shared.HookInterface),
	}
}

// DiscoverAndLoad finds plugins and connects to them.
// Should be called once during initialization.
func (m *Manager) DiscoverAndLoad() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.isLoaded {
		log.Println("Plugins already loaded.")
		return nil
	}

	log.Println("Discovering Mixy plugins...")

	pluginExecutables, err := m.findPluginExecutables()
	if err != nil {
		return fmt.Errorf("failed to find plugin executables: %w", err)
	}

	if len(pluginExecutables) == 0 {
		log.Println("No Mixy plugins found.")
		m.isLoaded = true
		return nil
	}

	log.Printf("Found potential plugins: %v\n", pluginExecutables)

	// --- Fix Start: Use hclog ---
	// Configure hclog logger for plugins
	pluginLogger := hclog.New(&hclog.LoggerOptions{
		Name:  "mixy-plugin",
		Level: hclog.Info, // Or hclog.Debug for more verbose output
		// Output: os.Stderr, // Default is stderr, customize if needed
	})
	// --- Fix End ---

	for _, path := range pluginExecutables {
		client := plugin.NewClient(&plugin.ClientConfig{
			HandshakeConfig: shared.Handshake,
			Plugins:         shared.PluginMap,
			Cmd:             exec.Command(path),
			Managed:         true,
			Logger:          pluginLogger, // Use the hclog logger here
			// SecureConfig: &plugin.SecureConfig{...}
		})
		// ... (rest of the loop remains the same) ...

		m.clients[path] = client // Store client for cleanup

		rpcClient, err := client.Client()
		if err != nil {
			// Use the hclog logger for plugin-related errors
			pluginLogger.Error("Error connecting to plugin", "path", path, "error", err)
			client.Kill()
			delete(m.clients, path)
			continue
		}

		// --- Plugin Dispensing Logic (using pluginLogger for errors) ---

		dispensedLoader := false
		rawLoader, err := rpcClient.Dispense(string(shared.LoaderPluginType))
		if err == nil {
			loader := rawLoader.(shared.LoaderInterface)
			meta, errMeta := loader.GetMetadata() // Renamed err to avoid shadowing outer err
			if errMeta != nil {
				pluginLogger.Error("Error getting metadata from loader plugin", "path", path, "error", errMeta)
			} else if meta.Type != shared.LoaderPluginType {
				pluginLogger.Warn("Plugin metadata type mismatch for loader", "plugin_name", meta.Name, "path", path, "metadata_type", meta.Type)
			} else {
				if _, exists := m.loaderPlugins[meta.Name]; exists {
					pluginLogger.Warn("Loader plugin name conflict", "plugin_name", meta.Name, "ignored_path", path)
				} else {
					pluginLogger.Info("Registered Loader Plugin", "name", meta.Name, "version", meta.Version, "path", path)
					m.loaderPlugins[meta.Name] = loader
					dispensedLoader = true
				}
			}
		} else if !strings.Contains(err.Error(), "unknown service") {
			pluginLogger.Error("Error dispensing loader interface", "path", path, "error", err)
		}

		dispensedHook := false
		rawHook, err := rpcClient.Dispense(string(shared.HookPluginType))
		if err == nil {
			hook := rawHook.(shared.HookInterface)
			meta, errMeta := hook.GetMetadata() // Renamed err
			if errMeta != nil {
				pluginLogger.Error("Error getting metadata from hook plugin", "path", path, "error", errMeta)
			} else if meta.Type != shared.HookPluginType {
				pluginLogger.Warn("Plugin metadata type mismatch for hook", "plugin_name", meta.Name, "path", path, "metadata_type", meta.Type)
			} else {
				if _, exists := m.hookPlugins[meta.Name]; exists {
					pluginLogger.Warn("Hook plugin name conflict", "plugin_name", meta.Name, "ignored_path", path)
				} else {
					pluginLogger.Info("Registered Hook Plugin", "name", meta.Name, "version", meta.Version, "path", path)
					m.hookPlugins[meta.Name] = hook
					dispensedHook = true
				}
			}
		} else if !strings.Contains(err.Error(), "unknown service") {
			pluginLogger.Error("Error dispensing hook interface", "path", path, "error", err)
		}

		if !dispensedLoader && !dispensedHook {
			pluginLogger.Warn("Plugin did not provide recognized interfaces. Unloading.", "path", path)
			client.Kill()
			delete(m.clients, path)
		}
	}

	m.isLoaded = true
	log.Println("Plugin discovery and loading complete.") // Keep using standard log for manager status
	return nil
}

// findPluginExecutables searches for files like "mixy-plugin-*"
func (m *Manager) findPluginExecutables() ([]string, error) {
	var paths []string
	seen := make(map[string]struct{}) // Avoid duplicates

	// 1. Search explicit plugin directory if provided
	if m.pluginDir != "" {
		absPluginDir, err := filepath.Abs(m.pluginDir)
		if err != nil {
			log.Printf("Warning: Cannot get absolute path for plugin directory '%s': %v\n", m.pluginDir, err)
		} else {
			files, err := os.ReadDir(absPluginDir)
			if err != nil && !os.IsNotExist(err) {
				log.Printf("Warning: Cannot read plugin directory '%s': %v\n", absPluginDir, err)
			} else if err == nil {
				for _, file := range files {
					if !file.IsDir() && strings.HasPrefix(file.Name(), "mixy-plugin-") {
						// Basic check for executable bit (might not be perfect cross-platform)
						info, err := file.Info()
						if err == nil && (info.Mode()&0111 != 0) {
							fullPath := filepath.Join(absPluginDir, file.Name())
							if _, ok := seen[fullPath]; !ok {
								paths = append(paths, fullPath)
								seen[fullPath] = struct{}{}
							}
						}
					}
				}
			}
		}
	}

	// 2. Search PATH environment variable
	sysPath := os.Getenv("PATH")
	pathDirs := filepath.SplitList(sysPath)
	for _, dir := range pathDirs {
		files, err := os.ReadDir(dir)
		if err != nil {
			continue // Ignore errors reading PATH directories
		}
		for _, file := range files {
			if !file.IsDir() && strings.HasPrefix(file.Name(), "mixy-plugin-") {
				// Basic check for executable bit
				info, err := file.Info()
				if err == nil && (info.Mode()&0111 != 0) {
					fullPath := filepath.Join(dir, file.Name())
					// Resolve symlinks to avoid duplicates if PATH has links
					resolvedPath, err := filepath.EvalSymlinks(fullPath)
					if err != nil {
						resolvedPath = fullPath // Use original if symlink fails
					}
					if _, ok := seen[resolvedPath]; !ok {
						paths = append(paths, resolvedPath)
						seen[resolvedPath] = struct{}{}
					}
				}
			}
		}
	}

	return paths, nil
}

// GetLoader checks if a loader plugin supports the given source.
// It uses the plugin name format "plugin:<name>:<plugin-specific-source>"
func (m *Manager) GetLoader(source string) (shared.LoaderInterface, string, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if !m.isLoaded {
		log.Println("Warning: Attempted to get loader plugin before loading finished.")
		return nil, "", false // Should ideally wait or error
	}

	// Check if source uses the plugin prefix format
	if !strings.HasPrefix(source, "plugin:") {
		return nil, "", false
	}

	parts := strings.SplitN(source, ":", 3)
	if len(parts) < 2 { // Need at least plugin:<name>
		log.Printf("Warning: Invalid plugin source format '%s'. Expected 'plugin:<name>[:<details>]'.\n", source)
		return nil, "", false
	}
	pluginName := parts[1]
	pluginSpecificSource := ""
	if len(parts) == 3 {
		pluginSpecificSource = parts[2]
	}

	if loader, ok := m.loaderPlugins[pluginName]; ok {
		// Optional: Ask the plugin if it *really* supports this specific source details
		// supported, err := loader.Supports(pluginSpecificSource) // This depends on how plugin.Supports is designed
		// if err != nil { log.Printf(...); return nil, false }
		// if supported { return loader, true }
		log.Printf("Found matching loader plugin '%s' for source '%s'\n", pluginName, source)
		return loader, pluginSpecificSource, true // Assume plugin handles the details passed to Load
	}

	return nil, "", false
}

// GetHook returns a specific hook plugin by name.
func (m *Manager) GetHook(name string) (shared.HookInterface, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if !m.isLoaded {
		log.Println("Warning: Attempted to get hook plugin before loading finished.")
		return nil, false
	}

	hook, ok := m.hookPlugins[name]
	return hook, ok
}

// Cleanup terminates all managed plugin processes.
func (m *Manager) Cleanup() {
	m.mu.Lock()
	defer m.mu.Unlock()
	log.Println("Cleaning up plugins...")
	plugin.CleanupClients()                     // This kills all managed clients started by plugin.NewClient
	m.clients = make(map[string]*plugin.Client) // Clear maps
	m.loaderPlugins = make(map[string]shared.LoaderInterface)
	m.hookPlugins = make(map[string]shared.HookInterface)
	m.isLoaded = false
	log.Println("Plugin cleanup complete.")
}

func (m *Manager) GetLoaderPluginByName(name string) (shared.LoaderInterface, bool) {
	m.mu.RLock() // Use RLock for read-only access
	defer m.mu.RUnlock()

	if !m.isLoaded {
		// Depending on desired behavior, you might want to log or wait
		log.Println("Warning: GetLoaderPluginByName called before plugins are loaded.")
		// Decide if this should return false or potentially block/error
	}

	loader, ok := m.loaderPlugins[name] // Access the map holding loaded loader plugins
	return loader, ok
}
