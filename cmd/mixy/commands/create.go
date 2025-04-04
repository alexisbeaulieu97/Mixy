// cmd/mixy/commands/create.go
package commands

import (
	"errors"
	"fmt"
	"log/slog"
	"os"
	"strings"

	"github.com/spf13/cobra"

	"github.com/alexisbeaulieu97/Mixy/internal/config"
	"github.com/alexisbeaulieu97/Mixy/internal/core"
	"github.com/alexisbeaulieu97/Mixy/internal/io"
	"github.com/alexisbeaulieu97/Mixy/internal/loader"
	"github.com/alexisbeaulieu97/Mixy/internal/merger"
	"github.com/alexisbeaulieu97/Mixy/internal/plugin"
	"github.com/alexisbeaulieu97/Mixy/internal/renderer"
	"github.com/alexisbeaulieu97/Mixy/internal/variables"
	"github.com/alexisbeaulieu97/Mixy/internal/workflow/resolver"
	"github.com/alexisbeaulieu97/Mixy/internal/workflow/steps"
)

var (
	outputDir     string
	variableFlags map[string]string
	logLevel      string
	logFormat     string
)

// createCmd implements the 'create' subcommand which handles project generation from templates.
// It coordinates the loading of configuration, template processing, and output generation
// through a series of workflow steps with middleware support.
var createCmd = &cobra.Command{
	Use:   "create <config_file>",
	Short: "Create a new project from templates defined in a config file.",
	Long:  `Loads template definitions and variables from the specified configuration file, processes them, and generates the final project structure using a step-based workflow with middleware support. Supports plugins.`,
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		configFile := args[0]

		var level slog.Level
		switch strings.ToLower(logLevel) {
		case "debug":
			level = slog.LevelDebug
		case "info":
			level = slog.LevelInfo
		case "warn":
			level = slog.LevelWarn
		case "error":
			level = slog.LevelError
		default:
			fmt.Fprintf(os.Stderr, "Warning: Invalid log level '%s', defaulting to 'info'\n", logLevel)
			level = slog.LevelInfo
		}

		var logger *slog.Logger
		opts := &slog.HandlerOptions{Level: level}
		if strings.ToLower(logFormat) == "json" {
			logger = slog.New(slog.NewJSONHandler(os.Stderr, opts))
		} else {
			logger = slog.New(slog.NewTextHandler(os.Stderr, opts))
		}
		logger = logger.With(slog.String("service", "mixy"))
		logger.Info("Initializing Mixy create command", slog.String("log_level", level.String()))

		pluginManager := plugin.NewManager("", logger)
		defer pluginManager.Cleanup()
		logger.Debug("Loading plugins")
		if err := pluginManager.DiscoverAndLoad(); err != nil {
			pluginLoadErr := core.NewPluginError("failed to initialize plugins", err)
			logger.Error("Failed to load plugins", slog.Any("error", pluginLoadErr))
			return pluginLoadErr
		}

		cfgSource := config.NewViperSource()
		varResolver := variables.NewBasicResolver()
		pluginLoaderAdapter := loader.NewPluginLoaderAdapter(pluginManager, logger)
		templateLoaders := []core.TemplateLoader{
			loader.NewLocalLoader(),
			pluginLoaderAdapter,
		}
		loaderResolver := resolver.NewBasicLoaderResolver(templateLoaders)
		templateRenderer := renderer.NewGoTemplateRenderer()
		templateMerger := merger.NewOverwriteMerger()
		outputWriter := io.NewDiskWriter()

		logger.Debug("Defining workflow steps")
		workflowSteps := []core.WorkflowStep{
			&steps.LoadConfigStep{ConfigSource: cfgSource},
			steps.NewResolveOutputDirStep(steps.OutputDirOptions{
				CreateIfMissing:     true,
				AllowParentCreation: true,
				RequireEmpty:        true,
				DefaultDir:          ".",
			}),
			&steps.ResolveVariablesStep{Resolver: varResolver},
			&steps.CreateTempDirStep{},
			&steps.ProcessTemplatesStep{Resolver: loaderResolver, Renderer: templateRenderer},
			&steps.MergeTemplatesStep{Merger: templateMerger},
			&steps.WriteOutputStep{Writer: outputWriter},
			&steps.RunHooksStep{PluginManager: pluginManager},
			&steps.FinalizeOutputStep{},
		}

		logger.Debug("Setting up workflow middleware")
		middleware := []core.WorkflowMiddleware{
			// Add concrete middleware instances here later, e.g.:
			// &middleware.LoggingMiddleware{},
			// &middleware.ErrorWrapperMiddleware{},
		}

		runner := core.NewWorkflowRunner(workflowSteps, middleware, logger)

		initialCtx := core.ProjectContext{
			ConfigFilePath:  configFile,
			OutputDirectory: outputDir,
			FlagVariables:   variableFlags,
			Logger:          logger,
		}

		logger.Info("Starting project creation workflow",
			slog.String("config_file", configFile),
			slog.String("output_dir_flag", outputDir),
			slog.Any("variable_flags", variableFlags),
		)

		err := runner.Run(initialCtx)
		if err != nil {
			if errors.Is(err, core.ErrCancelled) {
				fmt.Fprintln(os.Stderr, "Operation cancelled.")
				return err
			}
			return fmt.Errorf("project creation failed: %w", err)
		}

		logger.Info("Project created successfully!")
		fmt.Printf("\nProject created successfully in %s!\n", outputDir)
		return nil
	},
}

func init() {
	rootCmd.AddCommand(createCmd)
	createCmd.Flags().StringVarP(&outputDir, "output", "o", "", "Output directory for the generated project")
	createCmd.Flags().StringToStringVarP(&variableFlags, "var", "v", nil, "Override template variables (key=value)")
	createCmd.Flags().StringVar(&logLevel, "log-level", "info", "Set log level (debug, info, warn, error)")
	createCmd.Flags().StringVar(&logFormat, "log-format", "text", "Set log format (text, json)")
}
