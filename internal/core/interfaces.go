// internal/core/interfaces.go
package core

import (
	"io/fs"
	"log/slog" // Import slog

	"github.com/go-playground/validator/v10" // Import validator
)

const (
	// MixyConfigVersion defines the current config structure version Mixy understands.
	MixyConfigVersion = "1.0" // Start with 1.0
)

// ProjectContext holds runtime information for a Mixy execution.
type ProjectContext struct {
	// Input/Config provided by user/flags
	ConfigFilePath  string
	OutputDirectory string // Final desired output directory (absolute)
	FlagVariables   map[string]string

	// State built during workflow
	Config              *Config
	Variables           map[string]interface{}
	LoadedData          [][]TemplateData
	MergedData          []TemplateData
	TempOutputDirectory string // Added: Path to temporary output dir
	Logger              *slog.Logger
}

// TemplateData represents the content of a processed template file.
type TemplateData interface {
	Path() string // Relative path within the project structure
	Content() ([]byte, error)
	Mode() fs.FileMode // Added file mode
}

// Template represents a loaded, possibly unprocessed template source.
type Template interface {
	Source() string                                   // Identifier for the template source (e.g., path, URL)
	Load(ctx *ProjectContext) ([]TemplateData, error) // Loads raw data
}

// TemplateLoader is responsible for loading a template from a specific source type.
type TemplateLoader interface {
	Supports(source string) bool
	Load(source string, ctx *ProjectContext) (Template, error)
}

// TemplateRenderer applies variables to raw template data.
type TemplateRenderer interface {
	Render(raw TemplateData, variables map[string]interface{}, ctx *ProjectContext) (TemplateData, error)
}

// TemplateMerger combines multiple processed templates.
type TemplateMerger interface {
	Merge(templates [][]TemplateData, ctx *ProjectContext) ([]TemplateData, error)
}

// OutputWriter writes the final project structure to the destination.
type OutputWriter interface {
	Write(destination string, data []TemplateData, ctx *ProjectContext) error
}

// VariableResolver determines the final set of variables.
type VariableResolver interface {
	Resolve(
		configDefaults map[string]interface{},
		flagOverrides map[string]string,
		mandatoryKeys []string,
		ctx *ProjectContext, // Pass context for logging
	) (map[string]interface{}, error)
}

// --- Configuration Related ---

// Config represents the parsed configuration data.
type Config struct {
	Version            string                 `mapstructure:"version" validate:"required,eq=1.0"`       // Added version with validation
	Templates          []TemplateSource       `mapstructure:"templates" validate:"required,min=1,dive"` // Ensure at least one template, validate slice elements
	Variables          map[string]interface{} `mapstructure:"variables"`
	Output             string                 `mapstructure:"output"` // Validation can be added if needed (e.g., "omitempty,dirpath")
	Hooks              []string               `mapstructure:"hooks"`
	MandatoryVariables []string               `mapstructure:"mandatory_variables"`
}

// TemplateSource defines where to get a template from.
type TemplateSource struct {
	Source string `mapstructure:"source" validate:"required"` // Source path/URL/etc. is required
	Type   string `mapstructure:"type"`                       // Optional type hint
}

// Validate performs basic structural validation on the loaded config.
func (c *Config) Validate() error {
	validate := validator.New(validator.WithRequiredStructEnabled()) // Use playground validator
	err := validate.Struct(c)
	if err != nil {
		// Provide more user-friendly error messages if desired
		return NewValidationError("configuration validation failed", err)
	}
	// Add custom cross-field validation if needed here
	return nil
}

// ConfigSource defines the contract for loading Mixy configurations from a source.
type ConfigSource interface {
	Load(filePath string, logger *slog.Logger) (*Config, error)
}

// --- Placeholder Implementations ---

// InMemoryTemplateData provides a basic implementation for TemplateData.
type InMemoryTemplateData struct {
	FilePath string
	FileData []byte
	FileMode fs.FileMode // Added mode
}

func (d *InMemoryTemplateData) Path() string {
	return d.FilePath
}

func (d *InMemoryTemplateData) Content() ([]byte, error) {
	return d.FileData, nil
}

func (d *InMemoryTemplateData) Mode() fs.FileMode {
	// Return a default if not set, or ensure it's always set
	if d.FileMode == 0 {
		return 0644 // Default file mode
	}
	return d.FileMode
}

// NewInMemoryTemplateData creates a new instance.
func NewInMemoryTemplateData(path string, content []byte, mode fs.FileMode) TemplateData {
	if mode == 0 {
		mode = 0644 // Ensure a default mode
	}
	return &InMemoryTemplateData{FilePath: path, FileData: content, FileMode: mode}
}

type WorkflowStep interface {
	Execute(ctx *ProjectContext) error
	Name() string
}

type LoaderResolver interface {
	// Resolve determines the appropriate loader and the source string to pass to its Load method.
	Resolve(ts TemplateSource, logger *slog.Logger) (loader TemplateLoader, sourceForLoad string, err error)
}

type WorkflowHandler func(ctx *ProjectContext) error

// WorkflowMiddleware defines the interface for middleware that wraps workflow step execution.
type WorkflowMiddleware interface {
	Execute(ctx *ProjectContext, step WorkflowStep, next WorkflowHandler) error
}
