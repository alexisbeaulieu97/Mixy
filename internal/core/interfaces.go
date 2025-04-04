// Package core provides the foundational interfaces and types for Mixy's template-based
// project generation system.
package core

import (
	"io/fs"
	"log/slog"

	"github.com/go-playground/validator/v10"
)

// Version constants define supported configuration versions
const (
	// MixyConfigVersion is the current supported configuration version
	MixyConfigVersion = "1.0"
)

// Configuration types

// Config represents the parsed configuration data from a Mixy configuration file.
type Config struct {
	Version            string                 `mapstructure:"version" validate:"required,eq=1.0"`
	Templates          []TemplateSource       `mapstructure:"templates" validate:"required,min=1,dive"`
	Variables          map[string]interface{} `mapstructure:"variables"`
	Output             string                 `mapstructure:"output"`
	Hooks              []string               `mapstructure:"hooks"`
	MandatoryVariables []string               `mapstructure:"mandatory_variables"`
}

// TemplateSource defines where to get a template from and its type.
type TemplateSource struct {
	Source string `mapstructure:"source" validate:"required"`
	Type   string `mapstructure:"type"`
}

// ProjectContext holds runtime information for a Mixy execution.
// It maintains state throughout the workflow execution pipeline.
type ProjectContext struct {
	// Input configuration
	ConfigFilePath  string
	OutputDirectory string
	FlagVariables   map[string]string

	// Runtime state
	Config              *Config
	Variables           map[string]interface{}
	LoadedData          [][]TemplateData
	MergedData          []TemplateData
	TempOutputDirectory string
	Logger              *slog.Logger
}

// Template interfaces

// TemplateData represents the content of a processed template file.
type TemplateData interface {
	// Path returns the relative path of the template file
	Path() string
	// Content returns the processed template content
	Content() ([]byte, error)
	// Mode returns the file permissions to be used when writing the file
	Mode() fs.FileMode
}

// Template represents a loaded, possibly unprocessed template source.
type Template interface {
	// Source returns the original source location of the template
	Source() string
	// Load processes the template source and returns the template data
	Load(ctx *ProjectContext) ([]TemplateData, error)
}

// TemplateLoader is responsible for loading a template from a specific source type.
type TemplateLoader interface {
	// Supports checks if this loader can handle the given source type
	Supports(source string) bool
	// Load creates a Template instance from the given source
	Load(source string, ctx *ProjectContext) (Template, error)
}

// Processing interfaces

// TemplateRenderer applies variables to raw template data.
type TemplateRenderer interface {
	// Render processes the template with the given variables
	Render(raw TemplateData, variables map[string]interface{}, ctx *ProjectContext) (TemplateData, error)
}

// TemplateMerger combines multiple processed templates into a final set.
type TemplateMerger interface {
	// Merge combines multiple template datasets, resolving conflicts as needed
	Merge(templates [][]TemplateData, ctx *ProjectContext) ([]TemplateData, error)
}

// OutputWriter writes the final project structure to the destination.
type OutputWriter interface {
	// Write outputs the processed templates to the filesystem
	Write(destination string, data []TemplateData, ctx *ProjectContext) error
}

// VariableResolver determines the final set of variables for template processing.
type VariableResolver interface {
	// Resolve combines and processes variables from various sources
	Resolve(
		configDefaults map[string]interface{},
		flagOverrides map[string]string,
		mandatoryKeys []string,
		ctx *ProjectContext,
	) (map[string]interface{}, error)
}

// Workflow types

// WorkflowStep represents a single step in the template processing pipeline.
type WorkflowStep interface {
	// Execute performs the step's action
	Execute(ctx *ProjectContext) error
	// Name returns a human-readable identifier for the step
	Name() string
}

// WorkflowHandler represents a function that executes a workflow step.
type WorkflowHandler func(ctx *ProjectContext) error

// WorkflowMiddleware defines the interface for middleware that wraps workflow step execution.
type WorkflowMiddleware interface {
	// Execute runs the middleware's logic around the workflow step
	Execute(ctx *ProjectContext, step WorkflowStep, next WorkflowHandler) error
}

// ConfigSource defines the contract for loading Mixy configurations from a source.
type ConfigSource interface {
	// Load reads and parses a configuration file
	Load(filePath string, logger *slog.Logger) (*Config, error)
}

// LoaderResolver maps template sources to appropriate loaders.
type LoaderResolver interface {
	// Resolve determines the appropriate loader and normalized source for a template
	Resolve(ts TemplateSource, logger *slog.Logger) (loader TemplateLoader, sourceForLoad string, err error)
}

// Implementation types

// InMemoryTemplateData provides a basic implementation for TemplateData.
type InMemoryTemplateData struct {
	FilePath string
	FileData []byte
	FileMode fs.FileMode
}

func (d *InMemoryTemplateData) Path() string {
	return d.FilePath
}

func (d *InMemoryTemplateData) Content() ([]byte, error) {
	return d.FileData, nil
}

func (d *InMemoryTemplateData) Mode() fs.FileMode {
	if d.FileMode == 0 {
		return 0644
	}
	return d.FileMode
}

// NewInMemoryTemplateData creates a new instance of InMemoryTemplateData.
// If mode is 0, defaults to 0644 permissions.
func NewInMemoryTemplateData(path string, content []byte, mode fs.FileMode) TemplateData {
	if mode == 0 {
		mode = 0644
	}
	return &InMemoryTemplateData{FilePath: path, FileData: content, FileMode: mode}
}

// Validate performs basic structural validation on the loaded config.
func (c *Config) Validate() error {
	validate := validator.New(validator.WithRequiredStructEnabled())
	err := validate.Struct(c)
	if err != nil {
		return NewValidationError("configuration validation failed", err)
	}
	return nil
}
