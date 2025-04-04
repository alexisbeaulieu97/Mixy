// cmd/mixy/commands/create.go
package commands

import (
	"fmt"
	// Make sure log is needed/used, otherwise remove
	// Ensure all these paths are correct for your project structure
	"github.com/alexisbeaulieu97/Mixy/internal/config"
	"github.com/alexisbeaulieu97/Mixy/internal/core" // Import the core package
	"github.com/alexisbeaulieu97/Mixy/internal/io"
	"github.com/alexisbeaulieu97/Mixy/internal/loader"
	"github.com/alexisbeaulieu97/Mixy/internal/merger"
	"github.com/alexisbeaulieu97/Mixy/internal/plugin"
	"github.com/alexisbeaulieu97/Mixy/internal/renderer"
	"github.com/alexisbeaulieu97/Mixy/internal/variables"

	"github.com/spf13/cobra"
)

var (
	outputDir     string
	variableFlags map[string]string
)

var createCmd = &cobra.Command{
	Use:   "create <config_file>",
	Short: "Create a new project from templates defined in a config file.",
	Long:  `Loads template definitions and variables from the specified configuration file, processes them, and generates the final project structure. Supports plugins for loading and post-processing.`,
	Args:  cobra.ExactArgs(1), // Requires exactly one argument: the config file path
	RunE: func(cmd *cobra.Command, args []string) error {
		configFile := args[0]

		// --- Dependency Instantiation ---
		// Instantiate Plugin Manager
		pluginManager := plugin.NewManager("") // Scan PATH for now
		defer pluginManager.Cleanup()          // Ensure plugins are killed on exit

		// Discover and load plugins
		if err := pluginManager.DiscoverAndLoad(); err != nil {
			return fmt.Errorf("failed to load plugins: %w", err)
		}

		// Instantiate components using interfaces from the 'core' package
		var cfgLoader core.ConfigLoader = config.NewViperLoader()
		var varResolver core.VariableResolver = variables.NewBasicResolver()
		pluginLoaderAdapter := loader.NewPluginLoaderAdapter(pluginManager)
		var templateLoaders []core.TemplateLoader = []core.TemplateLoader{
			loader.NewLocalLoader(),
			pluginLoaderAdapter,
			// Add GitLoader later
		}
		var templateRenderer core.TemplateRenderer = renderer.NewGoTemplateRenderer()
		var templateMerger core.TemplateMerger = merger.NewOverwriteMerger()
		var outputWriter core.OutputWriter = io.NewDiskWriter()

		// Instantiate the Workflow using core.NewWorkflow
		workflow := core.NewWorkflow(
			cfgLoader,
			varResolver,
			templateLoaders,
			templateRenderer,
			templateMerger,
			outputWriter,
			pluginManager,
		)
		// --- End Dependency Instantiation ---

		// Prepare context using core.ProjectContext
		ctx := core.ProjectContext{
			ConfigFilePath:  configFile,
			OutputDirectory: outputDir,
			// Variables will be resolved within the workflow
		}

		fmt.Printf("Creating project from config: %s\n", configFile)
		if outputDir != "" {
			fmt.Printf("Output directory: %s\n", outputDir)
		}
		fmt.Printf("Variable overrides from flags: %v\n", variableFlags)

		// Execute the core workflow by calling Run on the workflow instance
		err := workflow.Run(ctx, variableFlags)
		if err != nil {
			return fmt.Errorf("project creation failed: %w", err) // Wrap error for context
		}

		fmt.Println("Project created successfully!")
		return nil
	},
}

func init() {
	rootCmd.AddCommand(createCmd)

	// Flag for output directory
	createCmd.Flags().StringVarP(&outputDir, "output", "o", "", "Output directory for the generated project (default: current directory or specified in config)")

	// Flag for variable overrides (e.g., -v name=value -v version=1.0)
	createCmd.Flags().StringToStringVarP(&variableFlags, "var", "v", nil, "Override template variables (key=value)")
}
