package core

// ProjectContext holds runtime information for a Mixy execution.
type ProjectContext struct {
	ConfigFilePath  string
	OutputDirectory string
	Variables       map[string]interface{} // Resolved variables
	// Potentially add logging, flags, etc. later
}

// TemplateData represents the content of a processed template file.
// Using an interface allows for different backing stores (memory, temp file).
type TemplateData interface {
	Path() string // Relative path within the project structure
	Content() ([]byte, error)
	// Mode() fs.FileMode // Consider adding file mode later
}

// Template represents a loaded, possibly unprocessed template source.
type Template interface {
	Source() string                                   // Identifier for the template source (e.g., path, URL)
	Load(ctx *ProjectContext) ([]TemplateData, error) // Loads raw data
}

// TemplateLoader is responsible for loading a template from a specific source type.
type TemplateLoader interface {
	// Supports determines if this loader can handle the given source string.
	Supports(source string) bool
	// Load fetches the template definition based on the source identifier.
	Load(source string, ctx *ProjectContext) (Template, error)
}

// TemplateRenderer applies variables to raw template data.
type TemplateRenderer interface {
	// Render processes a single template file's content.
	Render(raw TemplateData, variables map[string]interface{}) (TemplateData, error)
}

// TemplateMerger combines multiple processed templates.
type TemplateMerger interface {
	// Merge takes lists of processed TemplateData from various sources and combines them.
	// It needs to handle potential conflicts based on path.
	Merge(templates [][]TemplateData, ctx *ProjectContext) ([]TemplateData, error) // Returns the final list
}

// OutputWriter writes the final project structure to the destination.
type OutputWriter interface {
	Write(destination string, data []TemplateData) error
}

// VariableResolver determines the final set of variables.
type VariableResolver interface {
	// Resolve merges defaults, overrides, and prompts for missing mandatory variables.
	// Takes the list of mandatory keys defined in the config.
	Resolve(
		configDefaults map[string]interface{},
		flagOverrides map[string]string,
		mandatoryKeys []string, // Added mandatoryKeys
	) (map[string]interface{}, error)
}

// --- Placeholder Implementations (for initial structure) ---

// InMemoryTemplateData provides a basic implementation for TemplateData.
type InMemoryTemplateData struct {
	FilePath string
	FileData []byte
}

func (d *InMemoryTemplateData) Path() string {
	return d.FilePath
}

func (d *InMemoryTemplateData) Content() ([]byte, error) {
	return d.FileData, nil
}

// NewInMemoryTemplateData creates a new instance.
func NewInMemoryTemplateData(path string, content []byte) TemplateData {
	return &InMemoryTemplateData{FilePath: path, FileData: content}
}

// Config represents the parsed configuration data.
type Config struct {
	Templates          []TemplateSource       `mapstructure:"templates"`
	Variables          map[string]interface{} `mapstructure:"variables"`
	Output             string                 `mapstructure:"output"`
	Hooks              []string               `mapstructure:"hooks"`
	MandatoryVariables []string               `mapstructure:"mandatory_variables"` // Added
}

// TemplateSource defines where to get a template from.
type TemplateSource struct {
	Source string `mapstructure:"source"` // Path, URL, plugin identifier details
	Type   string `mapstructure:"type"`   // Optional: hint for loader type (e.g., "git", "local", "plugin:myloader")
}

// ConfigLoader defines the contract for loading Mixy configurations.
type ConfigLoader interface {
	Load(filePath string) (*Config, error)
}
