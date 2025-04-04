// pkg/plugin/shared.go
package plugin

import (
	"net/rpc"

	"github.com/hashicorp/go-plugin"
)

// Handshake is used to verify the plugin version compatibility.
var Handshake = plugin.HandshakeConfig{
	ProtocolVersion:  1,
	MagicCookieKey:   "MIXY_PLUGIN_MAGIC_COOKIE",
	MagicCookieValue: "mixy_plugin_f00d_cafe_babe", // Example cookie
}

// PluginType identifies the kind of plugin.
type PluginType string

const (
	LoaderPluginType PluginType = "loader"
	HookPluginType   PluginType = "hook"
	// Add other types later if needed
)

// PluginMetadata contains information about the plugin itself.
type PluginMetadata struct {
	Name        string
	Version     string
	Description string
	Type        PluginType
}

// PluginTemplateData is the RPC-safe version of core.TemplateData.
type PluginTemplateData struct {
	Path    string // Relative path
	Content []byte
	// Mode fs.FileMode // File mode can be complex over RPC, handle in host/plugin? Add later if needed.
}

// LoaderPluginContext holds information passed to loader plugins.
// Keep it simple and marshallable.
type LoaderPluginContext struct {
	Variables map[string]interface{}
	// Add other relevant simple fields from core.ProjectContext if needed
}

// LoaderInterface is the interface implemented by Template Loader plugins.
type LoaderInterface interface {
	// GetMetadata returns basic info about the plugin.
	GetMetadata() (PluginMetadata, error)
	// Supports determines if this loader can handle the given source string.
	Supports(source string) (bool, error)
	// Load fetches and potentially processes template data from the source.
	// It should return data ready for merging (variables might be applied here or by Mixy core).
	Load(source string, ctx LoaderPluginContext) ([]PluginTemplateData, error)
}

// HookPluginContext holds information passed to hook plugins.
type HookPluginContext struct {
	Variables       map[string]interface{}
	OutputDirectory string
	// Add other relevant simple fields from core.ProjectContext if needed
}

// HookInterface is the interface implemented by Post-Processing Hook plugins.
type HookInterface interface {
	// GetMetadata returns basic info about the plugin.
	GetMetadata() (PluginMetadata, error)
	// Execute runs the hook's action. hookType indicates when it's called (e.g., "PostGenerate").
	Execute(hookType string, ctx HookPluginContext) error
}

// --- RPC Server/Client Boilerplate (for go-plugin) ---

// LoaderPluginRPC is the RPC client implementation.
type LoaderPluginRPC struct{ client *rpc.Client }

func (g *LoaderPluginRPC) GetMetadata() (PluginMetadata, error) {
	var resp PluginMetadata
	err := g.client.Call("Plugin.GetMetadata", new(interface{}), &resp)
	return resp, err
}
func (g *LoaderPluginRPC) Supports(source string) (bool, error) {
	var resp bool
	err := g.client.Call("Plugin.Supports", source, &resp)
	return resp, err
}
func (g *LoaderPluginRPC) Load(source string, ctx LoaderPluginContext) ([]PluginTemplateData, error) {
	var resp []PluginTemplateData
	err := g.client.Call("Plugin.Load", map[string]interface{}{"source": source, "ctx": ctx}, &resp)
	return resp, err
}

// LoaderPluginServer is the RPC server implementation.
type LoaderPluginServer struct{ Impl LoaderInterface }

func (s *LoaderPluginServer) GetMetadata(args interface{}, resp *PluginMetadata) error {
	var err error
	*resp, err = s.Impl.GetMetadata()
	return err
}
func (s *LoaderPluginServer) Supports(source string, resp *bool) error {
	var err error
	*resp, err = s.Impl.Supports(source)
	return err
}
func (s *LoaderPluginServer) Load(args map[string]interface{}, resp *[]PluginTemplateData) error {
	var err error
	source := args["source"].(string)
	ctx := args["ctx"].(LoaderPluginContext) // Note: Relies on correct marshalling
	*resp, err = s.Impl.Load(source, ctx)
	return err
}

// LoaderPlugin is the go-plugin definition for Loaders.
type LoaderPlugin struct {
	Impl LoaderInterface
}

func (p *LoaderPlugin) Server(*plugin.MuxBroker) (interface{}, error) {
	return &LoaderPluginServer{Impl: p.Impl}, nil
}
func (LoaderPlugin) Client(b *plugin.MuxBroker, c *rpc.Client) (interface{}, error) {
	return &LoaderPluginRPC{client: c}, nil
}

// --- Hook Plugin RPC Boilerplate ---

// HookPluginRPC is the RPC client implementation.
type HookPluginRPC struct{ client *rpc.Client }

func (g *HookPluginRPC) GetMetadata() (PluginMetadata, error) {
	var resp PluginMetadata
	err := g.client.Call("Plugin.GetMetadata", new(interface{}), &resp)
	return resp, err
}
func (g *HookPluginRPC) Execute(hookType string, ctx HookPluginContext) error {
	err := g.client.Call("Plugin.Execute", map[string]interface{}{"hookType": hookType, "ctx": ctx}, nil)
	return err
}

// HookPluginServer is the RPC server implementation.
type HookPluginServer struct{ Impl HookInterface }

func (s *HookPluginServer) GetMetadata(args interface{}, resp *PluginMetadata) error {
	var err error
	*resp, err = s.Impl.GetMetadata()
	return err
}
func (s *HookPluginServer) Execute(args map[string]interface{}, resp *interface{}) error {
	hookType := args["hookType"].(string)
	ctx := args["ctx"].(HookPluginContext) // Note: Relies on correct marshalling
	return s.Impl.Execute(hookType, ctx)
}

// HookPlugin is the go-plugin definition for Hooks.
type HookPlugin struct {
	Impl HookInterface
}

func (p *HookPlugin) Server(*plugin.MuxBroker) (interface{}, error) {
	return &HookPluginServer{Impl: p.Impl}, nil
}
func (HookPlugin) Client(b *plugin.MuxBroker, c *rpc.Client) (interface{}, error) {
	return &HookPluginRPC{client: c}, nil
}

// PluginMap maps plugin names (used in discovery/config) to plugin definitions.
// Mixy core will use this to configure the plugin clients.
var PluginMap = map[string]plugin.Plugin{
	string(LoaderPluginType): &LoaderPlugin{},
	string(HookPluginType):   &HookPlugin{},
}
