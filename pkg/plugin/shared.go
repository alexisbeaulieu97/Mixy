// pkg/plugin/shared.go
package plugin

import (
	"net/rpc"

	"github.com/hashicorp/go-plugin"
)

// MixyPluginAPIVersion defines the API contract version between Mixy host and plugins.
// Increment this if LoaderInterface, HookInterface, or related structs change incompatibly.
const MixyPluginAPIVersion = "1.0"

// Handshake is used to verify the plugin version compatibility.
var Handshake = plugin.HandshakeConfig{
	ProtocolVersion:  1, // Keep this stable unless go-plugin protocol itself changes
	MagicCookieKey:   "MIXY_PLUGIN_MAGIC_COOKIE",
	MagicCookieValue: "mixy_plugin_v1_s3cur3", // Update cookie value slightly
}

// PluginType identifies the kind of plugin. Use defined constants.
type PluginType string

const (
	LoaderPluginType PluginType = "loader" // constant for loader plugin type
	HookPluginType   PluginType = "hook"   // constant for hook plugin type
)

// PluginMetadata contains information about the plugin itself.
type PluginMetadata struct {
	Name              string
	PluginVersion     string     // Version of the specific plugin implementation
	APIVersion        string     // API Version implemented by the plugin (e.g., "1.0")
	MixyCompatibility string     // Optional: e.g., Mixy version constraint (">= 1.2.0")
	Type              PluginType // Use the constant type
	Description       string
}

// --- Loader Plugin Interfaces/Structs ---

// PluginTemplateData is the RPC-safe version of core.TemplateData.
type PluginTemplateData struct {
	Path    string
	Content []byte
	Mode    uint32 // Use standard uint32 for RPC compatibility with fs.FileMode
}

// LoaderPluginContext holds information passed to loader plugins.
type LoaderPluginContext struct {
	Variables map[string]interface{}
	// Pass logger context? Might be complex over RPC. Host logs plugin calls.
}

// LoaderInterface is the interface implemented by Template Loader plugins.
type LoaderInterface interface {
	GetMetadata() (PluginMetadata, error)
	Supports(source string) (bool, error) // pluginSpecificSource passed here? Or in Load? Let's pass in Load.
	Load(pluginSpecificSource string, ctx LoaderPluginContext) ([]PluginTemplateData, error)
}

// --- Hook Plugin Interfaces/Structs ---

// HookPluginContext holds information passed to hook plugins.
type HookPluginContext struct {
	Variables       map[string]interface{}
	OutputDirectory string
}

// HookInterface is the interface implemented by Post-Processing Hook plugins.
type HookInterface interface {
	GetMetadata() (PluginMetadata, error)
	Execute(hookType string, ctx HookPluginContext) error
}

// --- RPC Server/Client Boilerplate (for go-plugin) ---
// --- Loader RPC ---

// LoaderPluginRPC is the RPC client implementation.
type LoaderPluginRPC struct{ client *rpc.Client }

func (g *LoaderPluginRPC) GetMetadata() (PluginMetadata, error) { /* ... no change ... */
	var resp PluginMetadata
	err := g.client.Call("Plugin.GetMetadata", new(interface{}), &resp)
	return resp, err
}
func (g *LoaderPluginRPC) Supports(source string) (bool, error) { /* ... no change ... */
	var resp bool
	err := g.client.Call("Plugin.Supports", source, &resp)
	return resp, err
}
func (g *LoaderPluginRPC) Load(pluginSpecificSource string, ctx LoaderPluginContext) ([]PluginTemplateData, error) { // Updated signature
	var resp []PluginTemplateData
	// Ensure map keys match server expectations
	err := g.client.Call("Plugin.Load", map[string]interface{}{"pluginSpecificSource": pluginSpecificSource, "ctx": ctx}, &resp)
	return resp, err
}

// LoaderPluginServer is the RPC server implementation.
type LoaderPluginServer struct{ Impl LoaderInterface }

func (s *LoaderPluginServer) GetMetadata(args interface{}, resp *PluginMetadata) error { /* ... no change ... */
	var err error
	*resp, err = s.Impl.GetMetadata()
	return err
}
func (s *LoaderPluginServer) Supports(source string, resp *bool) error { /* ... no change ... */
	var err error
	*resp, err = s.Impl.Supports(source)
	return err
}
func (s *LoaderPluginServer) Load(args map[string]interface{}, resp *[]PluginTemplateData) error { // Updated signature
	var err error
	pluginSpecificSource := args["pluginSpecificSource"].(string)
	// Need careful type assertion or marshalling for ctx
	var ctx LoaderPluginContext
	if ctxMap, ok := args["ctx"].(map[string]interface{}); ok {
		// Manual unmarshalling or use a library like mapstructure if complex
		if vars, ok := ctxMap["Variables"].(map[string]interface{}); ok {
			ctx.Variables = vars
		}
	} // Add error handling for type assertions

	*resp, err = s.Impl.Load(pluginSpecificSource, ctx) // Pass correctly typed args
	return err
}

// LoaderPlugin is the go-plugin definition for Loaders.
type LoaderPlugin struct {
	Impl LoaderInterface
}

func (p *LoaderPlugin) Server(*plugin.MuxBroker) (interface{}, error) { /* ... no change ... */
	return &LoaderPluginServer{Impl: p.Impl}, nil
}
func (LoaderPlugin) Client(b *plugin.MuxBroker, c *rpc.Client) (interface{}, error) { /* ... no change ... */
	return &LoaderPluginRPC{client: c}, nil
}

// --- Hook Plugin RPC Boilerplate ---

// HookPluginRPC is the RPC client implementation.
type HookPluginRPC struct{ client *rpc.Client }

func (g *HookPluginRPC) GetMetadata() (PluginMetadata, error) { /* ... no change ... */
	var resp PluginMetadata
	err := g.client.Call("Plugin.GetMetadata", new(interface{}), &resp)
	return resp, err
}
func (g *HookPluginRPC) Execute(hookType string, ctx HookPluginContext) error { /* ... no change ... */
	// Ensure map keys match server expectations
	err := g.client.Call("Plugin.Execute", map[string]interface{}{"hookType": hookType, "ctx": ctx}, nil)
	return err
}

// HookPluginServer is the RPC server implementation.
type HookPluginServer struct{ Impl HookInterface }

func (s *HookPluginServer) GetMetadata(args interface{}, resp *PluginMetadata) error { /* ... no change ... */
	var err error
	*resp, err = s.Impl.GetMetadata()
	return err
}
func (s *HookPluginServer) Execute(args map[string]interface{}, resp *interface{}) error { /* ... no change ... */
	hookType := args["hookType"].(string)
	// Careful type assertion/marshalling
	var ctx HookPluginContext
	if ctxMap, ok := args["ctx"].(map[string]interface{}); ok {
		if vars, ok := ctxMap["Variables"].(map[string]interface{}); ok {
			ctx.Variables = vars
		}
		if outDir, ok := ctxMap["OutputDirectory"].(string); ok {
			ctx.OutputDirectory = outDir
		}
	} // Add error handling

	return s.Impl.Execute(hookType, ctx)
}

// HookPlugin is the go-plugin definition for Hooks.
type HookPlugin struct {
	Impl HookInterface
}

func (p *HookPlugin) Server(*plugin.MuxBroker) (interface{}, error) { /* ... no change ... */
	return &HookPluginServer{Impl: p.Impl}, nil
}
func (HookPlugin) Client(b *plugin.MuxBroker, c *rpc.Client) (interface{}, error) { /* ... no change ... */
	return &HookPluginRPC{client: c}, nil
}

// PluginMap maps plugin names (used in discovery/config) to plugin definitions.
// Use constants for keys.
var PluginMap = map[string]plugin.Plugin{
	string(LoaderPluginType): &LoaderPlugin{}, // Use constant
	string(HookPluginType):   &HookPlugin{},   // Use constant
}
