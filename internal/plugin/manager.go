// internal/plugin/manager.go
package plugin

import (
	"errors" // Import standard errors
	"fmt"
	"log/slog"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"

	"github.com/hashicorp/go-hclog"
	"github.com/hashicorp/go-plugin"

	// REMOVE core import: "github.com/alexisbeaulieu97/Mixy/internal/core"
	shared "github.com/alexisbeaulieu97/Mixy/pkg/plugin" // Keep shared import
)

// slogToHclogWriter adapts slog.Logger to io.Writer interface used by hclog
type slogToHclogWriter struct {
	logger *slog.Logger
}

// Write implements io.Writer, converting hclog output to slog format
func (w slogToHclogWriter) Write(p []byte) (n int, err error) {
	w.logger.Info(strings.TrimSpace(string(p)))
	return len(p), nil
}

// Manager handles discovery and management of Mixy plugins.
type Manager struct {
	pluginDir     string
	clients       map[string]*plugin.Client
	loaderPlugins map[string]shared.LoaderInterface // Key is plugin name from metadata
	hookPlugins   map[string]shared.HookInterface   // Key is plugin name from metadata
	logger        *slog.Logger
	mu            sync.RWMutex
	isLoaded      bool
}

// NewManager creates a new plugin manager.
func NewManager(pluginDir string, logger *slog.Logger) *Manager {
	return &Manager{
		pluginDir:     pluginDir,
		clients:       make(map[string]*plugin.Client),
		loaderPlugins: make(map[string]shared.LoaderInterface),
		hookPlugins:   make(map[string]shared.HookInterface),
		logger:        logger.With(slog.String("component", "plugin_manager")),
	}
}

// DiscoverAndLoad finds plugins and connects to them.
// Returns standard errors; caller should wrap if necessary.
func (m *Manager) DiscoverAndLoad() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.isLoaded {
		m.logger.Debug("Plugins already loaded.")
		return nil
	}

	m.logger.Info("Discovering Mixy plugins...")

	pluginExecutables, err := m.findPluginExecutables()
	if err != nil {
		m.logger.Error("Failed to find plugin executables", slog.Any("error", err))
		// Return standard error
		return fmt.Errorf("plugin discovery failed: %w", err)
	}

	if len(pluginExecutables) == 0 {
		m.logger.Info("No Mixy plugins found.")
		m.isLoaded = true
		return nil
	}

	m.logger.Info("Found potential plugins", slog.Any("paths", pluginExecutables))

	// Create an hclog adapter that wraps our slog.Logger
	hclogAdapter := hclog.New(&hclog.LoggerOptions{
		Name:   "plugin",
		Level:  hclog.Info,
		Output: slogToHclogWriter{logger: m.logger.With(slog.String("source", "go-plugin"))},
	})

	for _, path := range pluginExecutables {
		logger := m.logger.With(slog.String("plugin_path", path))
		client := plugin.NewClient(&plugin.ClientConfig{
			HandshakeConfig: shared.Handshake,
			Plugins:         shared.PluginMap,
			Cmd:             exec.Command(path),
			Managed:         true,
			Logger:          hclogAdapter,
		})
		m.clients[path] = client

		logger.Debug("Attempting to connect to plugin")
		rpcClient, err := client.Client()
		if err != nil {
			logger.Error("Error connecting to plugin RPC", slog.Any("error", err))
			client.Kill()
			delete(m.clients, path)
			continue // Skip this plugin
		}

		dispensedSomething := false

		// Try Loader
		logger.Debug("Attempting to dispense loader interface")
		rawLoader, err := rpcClient.Dispense(string(shared.LoaderPluginType))
		if err == nil {
			loader := rawLoader.(shared.LoaderInterface)
			meta, errMeta := loader.GetMetadata()
			if errMeta != nil {
				logger.Error("Error getting metadata from loader plugin", slog.Any("error", errMeta))
				// Decide if this is fatal for the plugin. Let's skip it.
			} else if errVal := m.validateMetadata(meta, shared.LoaderPluginType, path, logger); errVal == nil {
				if _, exists := m.loaderPlugins[meta.Name]; exists {
					logger.Warn("Loader plugin name conflict. Ignoring plugin.", slog.String("plugin_name", meta.Name))
				} else {
					logger.Info("Registered Loader Plugin", slog.String("name", meta.Name), slog.String("plugin_version", meta.PluginVersion), slog.String("api_version", meta.APIVersion))
					m.loaderPlugins[meta.Name] = loader
					dispensedSomething = true
				}
			} // validateMetadata logs errors and returns standard error
		} else if !strings.Contains(err.Error(), "unknown service") {
			logger.Error("Error dispensing loader interface", slog.Any("error", err))
		}

		// Try Hook
		logger.Debug("Attempting to dispense hook interface")
		rawHook, err := rpcClient.Dispense(string(shared.HookPluginType))
		if err == nil {
			hook := rawHook.(shared.HookInterface)
			meta, errMeta := hook.GetMetadata()
			if errMeta != nil {
				logger.Error("Error getting metadata from hook plugin", slog.Any("error", errMeta))
			} else if errVal := m.validateMetadata(meta, shared.HookPluginType, path, logger); errVal == nil {
				if _, exists := m.hookPlugins[meta.Name]; exists {
					logger.Warn("Hook plugin name conflict. Ignoring plugin.", slog.String("plugin_name", meta.Name))
				} else {
					logger.Info("Registered Hook Plugin", slog.String("name", meta.Name), slog.String("plugin_version", meta.PluginVersion), slog.String("api_version", meta.APIVersion))
					m.hookPlugins[meta.Name] = hook
					dispensedSomething = true
				}
			}
		} else if !strings.Contains(err.Error(), "unknown service") {
			logger.Error("Error dispensing hook interface", slog.Any("error", err))
		}

		if !dispensedSomething {
			logger.Warn("Plugin did not provide any recognized & valid Mixy plugin interfaces. Unloading.", slog.String("path", path))
			client.Kill()
			delete(m.clients, path)
		}
	}

	m.isLoaded = true
	m.logger.Info("Plugin discovery and loading complete.")
	return nil // Success
}

// validateMetadata checks required fields and API version compatibility.
// Returns standard errors.
func (m *Manager) validateMetadata(meta shared.PluginMetadata, expectedType shared.PluginType, path string, logger *slog.Logger) error {
	if meta.Name == "" {
		logger.Error("Plugin metadata validation failed: Name is missing.", slog.String("plugin_path", path))
		return errors.New("plugin name missing")
	}
	if meta.APIVersion == "" {
		logger.Error("Plugin metadata validation failed: APIVersion is missing.", slog.String("plugin_name", meta.Name))
		return errors.New("plugin APIVersion missing")
	}
	if meta.Type != expectedType {
		logger.Error("Plugin metadata validation failed: Type mismatch.", slog.String("plugin_name", meta.Name), slog.String("expected_type", string(expectedType)), slog.String("actual_type", string(meta.Type)))
		return errors.New("plugin type mismatch")
	}

	// --- API Version Check ---
	if meta.APIVersion != shared.MixyPluginAPIVersion {
		errMsg := fmt.Sprintf("plugin '%s' API version '%s' incompatible with host API version '%s'", meta.Name, meta.APIVersion, shared.MixyPluginAPIVersion)
		logger.Error("Plugin API version mismatch.",
			slog.String("plugin_name", meta.Name),
			slog.String("plugin_api_version", meta.APIVersion),
			slog.String("host_api_version", shared.MixyPluginAPIVersion),
		)
		// Return standard error
		return errors.New(errMsg)
	}

	logger.Debug("Plugin metadata validated successfully", slog.String("plugin_name", meta.Name))
	return nil
}

// findPluginExecutables searches for files like "mixy-plugin-*"
// Returns standard errors.
func (m *Manager) findPluginExecutables() ([]string, error) {
	var paths []string
	seen := make(map[string]struct{})

	// 1. Search explicit plugin directory
	if m.pluginDir != "" {
		absPluginDir, err := filepath.Abs(m.pluginDir)
		if err != nil {
			m.logger.Warn("Cannot get absolute path for plugin directory", "dir", m.pluginDir, "error", err)
			// Continue searching PATH
		} else {
			m.logger.Debug("Scanning plugin directory", "dir", absPluginDir)
			files, err := os.ReadDir(absPluginDir)
			if err != nil && !os.IsNotExist(err) {
				m.logger.Warn("Cannot read plugin directory", "dir", absPluginDir, "error", err)
				// Continue searching PATH
			} else if err == nil {
				for _, file := range files {
					if !file.IsDir() && strings.HasPrefix(file.Name(), "mixy-plugin-") {
						info, errInfo := file.Info()
						if errInfo == nil && (info.Mode()&0111 != 0) {
							fullPath := filepath.Join(absPluginDir, file.Name())
							if _, ok := seen[fullPath]; !ok {
								m.logger.Debug("Found potential plugin", "path", fullPath)
								paths = append(paths, fullPath)
								seen[fullPath] = struct{}{}
							}
						}
					}
				}
			}
		}
	} else {
		m.logger.Debug("No explicit plugin directory specified, searching PATH.")
	}

	// 2. Search PATH
	sysPath := os.Getenv("PATH")
	pathDirs := filepath.SplitList(sysPath)
	m.logger.Debug("Scanning PATH directories", slog.Int("count", len(pathDirs)))
	for _, dir := range pathDirs {
		files, err := os.ReadDir(dir)
		if err != nil {
			continue
		} // Ignore errors reading PATH directories
		for _, file := range files {
			if !file.IsDir() && strings.HasPrefix(file.Name(), "mixy-plugin-") {
				info, errInfo := file.Info()
				if errInfo == nil && (info.Mode()&0111 != 0) {
					fullPath := filepath.Join(dir, file.Name())
					resolvedPath, errLink := filepath.EvalSymlinks(fullPath)
					if errLink != nil {
						resolvedPath = fullPath
					}
					if _, ok := seen[resolvedPath]; !ok {
						m.logger.Debug("Found potential plugin in PATH", "path", resolvedPath)
						paths = append(paths, resolvedPath)
						seen[resolvedPath] = struct{}{}
					}
				}
			}
		}
	}

	if len(paths) == 0 {
		m.logger.Debug("No plugin executables found in explicit directory or PATH.")
	}
	return paths, nil // No error if simply not found
}

// GetLoader checks if a loader plugin supports the given source.
func (m *Manager) GetLoader(source string) (loader shared.LoaderInterface, pluginSpecificSource string, ok bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if !m.isLoaded {
		m.logger.Warn("Attempted to get loader plugin before loading finished.")
		return nil, "", false
	}

	if !strings.HasPrefix(source, "plugin:") {
		return nil, "", false
	}

	parts := strings.SplitN(source, ":", 3)
	if len(parts) < 2 {
		m.logger.Warn("Invalid plugin source format. Expected 'plugin:<name>[:<details>]'.", "source", source)
		return nil, "", false
	}
	pluginName := parts[1]
	details := ""
	if len(parts) == 3 {
		details = parts[2]
	}

	loader, found := m.loaderPlugins[pluginName]
	if found {
		m.logger.Debug("Found matching loader plugin", "plugin_name", pluginName, "source_details", details)
		return loader, details, true
	}

	m.logger.Debug("No loader plugin found matching name", "plugin_name", pluginName)
	return nil, "", false
}

// GetHook returns a specific hook plugin by name.
func (m *Manager) GetHook(name string) (shared.HookInterface, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if !m.isLoaded {
		m.logger.Warn("Attempted to get hook plugin before loading finished.")
		return nil, false
	}

	hook, ok := m.hookPlugins[name]
	if ok {
		m.logger.Debug("Found hook plugin", "hook_name", name)
	} else {
		m.logger.Debug("Hook plugin not found", "hook_name", name)
	}
	return hook, ok
}

// Cleanup terminates all managed plugin processes.
func (m *Manager) Cleanup() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.logger.Info("Cleaning up plugins...")
	plugin.CleanupClients()
	m.clients = make(map[string]*plugin.Client)
	m.loaderPlugins = make(map[string]shared.LoaderInterface)
	m.hookPlugins = make(map[string]shared.HookInterface)
	m.isLoaded = false
	m.logger.Info("Plugin cleanup complete.")
}
