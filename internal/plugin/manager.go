// internal/plugin/manager.go
package plugin

import (
	"context"
	"errors" // Import standard errors
	"fmt"
	"log/slog"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

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

// Custom error types for better error handling
type PluginError struct {
	Err     error
	Plugin  string
	Code    string
	Details map[string]interface{}
}

func (e *PluginError) Error() string {
	return fmt.Sprintf("[%s] %s: %v", e.Code, e.Plugin, e.Err)
}

// Plugin states for lifecycle management
type PluginState int

const (
	StateUnknown PluginState = iota
	StateDiscovered
	StateValidated
	StateLoaded
	StateFailed
)

// PluginInfo tracks plugin metadata and state
type PluginInfo struct {
	Path     string
	State    PluginState
	Metadata shared.PluginMetadata
	Client   *plugin.Client
	LastErr  error
}

// Manager handles discovery and management of Mixy plugins.
type Manager struct {
	config        PluginConfig
	plugins       map[string]*PluginInfo            // Key is plugin path
	loaderPlugins map[string]shared.LoaderInterface // Key is plugin name from metadata
	hookPlugins   map[string]shared.HookInterface   // Key is plugin name from metadata
	logger        *slog.Logger
	mu            sync.RWMutex
	isLoaded      bool
}

// PluginConfig allows customizing plugin behavior
type PluginConfig struct {
	PluginDirs        []string      // Multiple plugin directories
	PluginPattern     string        // Configurable plugin naming pattern
	LoadTimeout       time.Duration // Timeout for plugin loading
	ValidationOptions ValidationOptions
}

type ValidationOptions struct {
	RequireSignature bool              // Require plugins to be signed
	AllowedVersions  []string          // Allowed API versions
	CustomValidators []PluginValidator // Custom validation functions
}

type PluginValidator func(*PluginInfo) error

// NewManager creates a new plugin manager with the given configuration.
func NewManager(config PluginConfig, logger *slog.Logger) *Manager {
	if config.PluginPattern == "" {
		config.PluginPattern = "mixy-plugin-*"
	}
	if config.LoadTimeout == 0 {
		config.LoadTimeout = 30 * time.Second
	}

	return &Manager{
		config:        config,
		plugins:       make(map[string]*PluginInfo),
		loaderPlugins: make(map[string]shared.LoaderInterface),
		hookPlugins:   make(map[string]shared.HookInterface),
		logger:        logger.With(slog.String("component", "plugin_manager")),
	}
}

// DiscoverAndLoad finds plugins and connects to them concurrently.
func (m *Manager) DiscoverAndLoad() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.isLoaded {
		m.logger.Debug("Plugins already loaded.")
		return nil
	}

	ctx, cancel := context.WithTimeout(context.Background(), m.config.LoadTimeout)
	defer cancel()

	m.logger.Info("Starting plugin discovery...")

	// Discover plugins
	plugins, err := m.discoverPlugins(ctx)
	if err != nil {
		return &PluginError{
			Err:  err,
			Code: "DISCOVERY_FAILED",
			Details: map[string]interface{}{
				"dirs": m.config.PluginDirs,
			},
		}
	}

	if len(plugins) == 0 {
		m.logger.Info("No plugins found.")
		m.isLoaded = true
		return nil
	}

	m.logger.Info("Found plugins", slog.Int("count", len(plugins)))

	// Load plugins concurrently
	var wg sync.WaitGroup
	errChan := make(chan error, len(plugins))

	for _, pluginPath := range plugins {
		wg.Add(1)
		go func(path string) {
			defer wg.Done()
			if err := m.loadPlugin(ctx, path); err != nil {
				errChan <- err
			}
		}(pluginPath)
	}

	// Wait for all plugins to load or context timeout
	doneChan := make(chan struct{})
	go func() {
		wg.Wait()
		close(doneChan)
	}()

	select {
	case <-ctx.Done():
		return &PluginError{
			Err:  ctx.Err(),
			Code: "LOAD_TIMEOUT",
		}
	case err := <-errChan:
		return err
	case <-doneChan:
		// All plugins loaded successfully
	}

	m.isLoaded = true
	m.logger.Info("Plugin discovery and loading complete.")
	return nil
}

// discoverPlugins finds all plugin executables in configured directories
func (m *Manager) discoverPlugins(ctx context.Context) ([]string, error) {
	var paths []string
	seen := make(map[string]struct{})

	// Search configured plugin directories
	for _, dir := range m.config.PluginDirs {
		absDir, err := filepath.Abs(dir)
		if err != nil {
			m.logger.Warn("Cannot get absolute path for plugin directory", "dir", dir, "error", err)
			continue
		}

		m.logger.Debug("Scanning plugin directory", "dir", absDir)
		files, err := os.ReadDir(absDir)
		if err != nil && !os.IsNotExist(err) {
			m.logger.Warn("Cannot read plugin directory", "dir", absDir, "error", err)
			continue
		}

		for _, file := range files {
			if !file.IsDir() && strings.HasPrefix(file.Name(), m.config.PluginPattern) {
				info, errInfo := file.Info()
				if errInfo == nil && (info.Mode()&0111 != 0) {
					fullPath := filepath.Join(absDir, file.Name())
					if _, ok := seen[fullPath]; !ok {
						paths = append(paths, fullPath)
						seen[fullPath] = struct{}{}
					}
				}
			}
		}
	}

	// Search PATH as fallback if no plugins found
	if len(paths) == 0 {
		sysPath := os.Getenv("PATH")
		for _, dir := range filepath.SplitList(sysPath) {
			files, err := os.ReadDir(dir)
			if err != nil {
				continue
			}
			for _, file := range files {
				if !file.IsDir() && strings.HasPrefix(file.Name(), m.config.PluginPattern) {
					info, errInfo := file.Info()
					if errInfo == nil && (info.Mode()&0111 != 0) {
						fullPath := filepath.Join(dir, file.Name())
						resolvedPath, errLink := filepath.EvalSymlinks(fullPath)
						if errLink != nil {
							resolvedPath = fullPath
						}
						if _, ok := seen[resolvedPath]; !ok {
							paths = append(paths, resolvedPath)
							seen[resolvedPath] = struct{}{}
						}
					}
				}
			}
		}
	}

	return paths, nil
}

// loadPlugin initializes and validates a single plugin
func (m *Manager) loadPlugin(ctx context.Context, path string) error {
	logger := m.logger.With(slog.String("plugin_path", path))

	// Create plugin info
	info := &PluginInfo{
		Path:  path,
		State: StateDiscovered,
	}
	m.plugins[path] = info

	// Create hclog adapter
	hclogAdapter := hclog.New(&hclog.LoggerOptions{
		Name:   "plugin",
		Level:  hclog.Info,
		Output: slogToHclogWriter{logger: logger.With(slog.String("source", "go-plugin"))},
	})

	// Initialize plugin client
	client := plugin.NewClient(&plugin.ClientConfig{
		HandshakeConfig: shared.Handshake,
		Plugins:         shared.PluginMap,
		Cmd:             exec.Command(path),
		Managed:         true,
		Logger:          hclogAdapter,
	})
	info.Client = client

	logger.Debug("Attempting to connect to plugin")
	rpcClient, err := client.Client()
	if err != nil {
		info.State = StateFailed
		info.LastErr = err
		logger.Error("Error connecting to plugin RPC", slog.Any("error", err))
		client.Kill()
		return &PluginError{
			Err:    err,
			Plugin: path,
			Code:   "RPC_CONNECTION_FAILED",
		}
	}

	dispensedSomething := false

	// Try Loader interface
	logger.Debug("Attempting to dispense loader interface")
	rawLoader, err := rpcClient.Dispense(string(shared.LoaderPluginType))
	if err == nil {
		loader := rawLoader.(shared.LoaderInterface)
		meta, errMeta := loader.GetMetadata()
		if errMeta != nil {
			logger.Error("Error getting metadata from loader plugin", slog.Any("error", errMeta))
		} else if errVal := m.validateMetadata(meta, shared.LoaderPluginType, path, logger); errVal == nil {
			if _, exists := m.loaderPlugins[meta.Name]; exists {
				logger.Warn("Loader plugin name conflict", slog.String("plugin_name", meta.Name))
			} else {
				info.State = StateValidated
				info.Metadata = meta
				m.loaderPlugins[meta.Name] = loader
				dispensedSomething = true
			}
		}
	} else if !strings.Contains(err.Error(), "unknown service") {
		logger.Error("Error dispensing loader interface", slog.Any("error", err))
	}

	// Try Hook interface
	logger.Debug("Attempting to dispense hook interface")
	rawHook, err := rpcClient.Dispense(string(shared.HookPluginType))
	if err == nil {
		hook := rawHook.(shared.HookInterface)
		meta, errMeta := hook.GetMetadata()
		if errMeta != nil {
			logger.Error("Error getting metadata from hook plugin", slog.Any("error", errMeta))
		} else if errVal := m.validateMetadata(meta, shared.HookPluginType, path, logger); errVal == nil {
			if _, exists := m.hookPlugins[meta.Name]; exists {
				logger.Warn("Hook plugin name conflict", slog.String("plugin_name", meta.Name))
			} else {
				info.State = StateValidated
				info.Metadata = meta
				m.hookPlugins[meta.Name] = hook
				dispensedSomething = true
			}
		}
	} else if !strings.Contains(err.Error(), "unknown service") {
		logger.Error("Error dispensing hook interface", slog.Any("error", err))
	}

	if !dispensedSomething {
		info.State = StateFailed
		info.LastErr = errors.New("no valid plugin interfaces found")
		logger.Warn("Plugin did not provide any recognized & valid Mixy plugin interfaces")
		client.Kill()
		return &PluginError{
			Err:    info.LastErr,
			Plugin: path,
			Code:   "NO_VALID_INTERFACES",
		}
	}

	info.State = StateLoaded
	return nil
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

	// Kill all plugin processes
	for _, info := range m.plugins {
		if info.Client != nil {
			info.Client.Kill()
		}
	}

	plugin.CleanupClients()
	m.plugins = make(map[string]*PluginInfo)
	m.loaderPlugins = make(map[string]shared.LoaderInterface)
	m.hookPlugins = make(map[string]shared.HookInterface)
	m.isLoaded = false
	m.logger.Info("Plugin cleanup complete.")
}
