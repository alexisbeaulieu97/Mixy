// internal/core/workflow.go
package core

import (
	"errors"
	"fmt"
	"log"
	"path/filepath"
	"strings"

	"github.com/alexisbeaulieu97/Mixy/internal/plugin"
	"github.com/alexisbeaulieu97/Mixy/internal/tui"
	pkg_plugin "github.com/alexisbeaulieu97/Mixy/pkg/plugin"
)

// Workflow orchestrates the template processing pipeline.
type Workflow struct {
	configLoader     ConfigLoader
	variableResolver VariableResolver
	templateLoaders  []TemplateLoader
	templateRenderer TemplateRenderer
	templateMerger   TemplateMerger
	outputWriter     OutputWriter
	pluginManager    *plugin.Manager
}

// NewWorkflow creates a new instance of the Workflow with all required dependencies.
func NewWorkflow(
	configLoader ConfigLoader,
	variableResolver VariableResolver,
	templateLoaders []TemplateLoader,
	templateRenderer TemplateRenderer,
	templateMerger TemplateMerger,
	outputWriter OutputWriter,
	pluginManager *plugin.Manager,
) *Workflow {
	return &Workflow{
		configLoader:     configLoader,
		variableResolver: variableResolver,
		templateLoaders:  templateLoaders,
		templateRenderer: templateRenderer,
		templateMerger:   templateMerger,
		outputWriter:     outputWriter,
		pluginManager:    pluginManager,
	}
}

// Run executes the main Mixy workflow.
func (w *Workflow) Run(initialCtx ProjectContext, flagVariables map[string]string) error {
	// --- Steps 1-3: Load Config, Determine Output, Resolve Vars (No changes needed here) ---
	cfg, err := w.configLoader.Load(initialCtx.ConfigFilePath)
	if err != nil {
		return fmt.Errorf("failed to load configuration: %w", err)
	}

	outputDir := "."
	if cfg.Output != "" {
		outputDir = cfg.Output
	}
	if initialCtx.OutputDirectory != "" {
		outputDir = initialCtx.OutputDirectory
	}
	absOutputDir, err := filepath.Abs(outputDir)
	if err != nil {
		return fmt.Errorf("failed to determine absolute output path for '%s': %w", outputDir, err)
	}
	initialCtx.OutputDirectory = absOutputDir

	resolvedVars, err := w.variableResolver.Resolve(cfg.Variables, flagVariables, cfg.MandatoryVariables) // Pass mandatory keys
	if err != nil {
		// Check if the error is user cancellation to provide a cleaner exit message
		if errors.Is(err, tui.ErrUserCancelled) { // Assuming tui.ErrUserCancelled is accessible or redefine it in core/errors
			fmt.Println("Operation cancelled by user during variable input.")
			// Return a distinct error or nil depending on desired CLI behavior on cancel
			// Returning the specific error allows the caller (main) to potentially exit quietly.
			return err
		}
		return fmt.Errorf("failed to resolve variables: %w", err)
	}
	initialCtx.Variables = resolvedVars // Update context with final variables

	// 4. Process Templates (Load -> Render)
	allProcessedTemplates := make([][]TemplateData, 0, len(cfg.Templates))
	for i, ts := range cfg.Templates { // Loop through template sources defined in config
		fmt.Printf("Processing template source %d: %s (Type hint: %s)\n", i+1, ts.Source, ts.Type)

		var loader TemplateLoader   // Variable to hold the found loader instance
		var sourceToUse = ts.Source // The string to pass to Supports/Load

		// --- Simplified Loader Selection Logic ---
		// If the user provides a 'type' hint starting with 'plugin:', construct
		// the 'plugin:<name>:<source>' string that the PluginLoaderAdapter expects.
		// Otherwise, just use the original source string.
		if ts.Type != "" && strings.HasPrefix(ts.Type, "plugin:") {
			pluginName := strings.TrimPrefix(ts.Type, "plugin:")
			if pluginName != "" { // Avoid creating "plugin::source" if type is just "plugin:"
				sourceToUse = fmt.Sprintf("plugin:%s:%s", pluginName, ts.Source)
				log.Printf("Type hint provided, using combined source for loader check: %s\n", sourceToUse)
			} else {
				log.Printf("Warning: Invalid plugin type hint '%s' for source '%s'. Using original source.", ts.Type, ts.Source)
			}
		}

		// Iterate through all registered loaders (e.g., LocalLoader, PluginLoaderAdapter)
		for _, l := range w.templateLoaders {
			// Ask the loader instance directly if it supports the source string.
			// The PluginLoaderAdapter.Supports will check for "plugin:..." format,
			// while other loaders (like LocalLoader) will check for file paths etc.
			if l.Supports(sourceToUse) {
				loader = l // Found the correct loader
				log.Printf("Selected loader %T for source '%s'\n", loader, sourceToUse)
				break // Exit the inner loader selection loop
			}
		}
		// --- End Simplified Loader Selection Logic ---

		// Check if any loader claimed the source
		if loader == nil {
			// Use sourceToUse in error message as that's what we tested
			return fmt.Errorf("no loader found that supports source: %s (Original source: %s, Type hint: %s)", sourceToUse, ts.Source, ts.Type)
		}

		// --- Use the assigned loader instance ---
		// Call Load using the source string the loader said it supported.
		// The PluginLoaderAdapter's Load method knows how to parse the "plugin:..." format back apart.
		template, err := loader.Load(sourceToUse, &initialCtx)
		if err != nil {
			return fmt.Errorf("failed to load template definition from '%s' using loader %T: %w", sourceToUse, loader, err)
		}

		// Load the actual file content using the returned Template object
		rawTemplateFiles, err := template.Load(&initialCtx)
		if err != nil {
			// Use template.Source() here, which should return the identifier (e.g., file path or original plugin:...)
			return fmt.Errorf("failed to load content for template source '%s': %w", template.Source(), err)
		}

		// Render each file in the loaded template
		processedTemplateFiles := make([]TemplateData, 0, len(rawTemplateFiles))
		for _, rawFile := range rawTemplateFiles {
			fmt.Printf("  Rendering file: %s\n", rawFile.Path())
			processedFile, err := w.templateRenderer.Render(rawFile, initialCtx.Variables)
			if err != nil {
				return fmt.Errorf("failed to render file '%s' from template source '%s': %w", rawFile.Path(), template.Source(), err)
			}
			processedTemplateFiles = append(processedTemplateFiles, processedFile)
		}
		allProcessedTemplates = append(allProcessedTemplates, processedTemplateFiles)

	} // End outer loop (processing template sources)

	// --- Steps 5-7: Merge, Write, Hooks (No changes needed here) ---
	fmt.Println("Merging processed templates...")
	finalProjectData, err := w.templateMerger.Merge(allProcessedTemplates, &initialCtx)
	if err != nil {
		return fmt.Errorf("failed to merge templates: %w", err)
	}
	fmt.Printf("Merging complete. Final file count: %d\n", len(finalProjectData))

	fmt.Printf("Writing final project to: %s\n", initialCtx.OutputDirectory)
	if err := w.outputWriter.Write(initialCtx.OutputDirectory, finalProjectData); err != nil {
		return fmt.Errorf("failed to write project output: %w", err)
	}

	if len(cfg.Hooks) > 0 {
		fmt.Println("Executing post-processing hooks...")
		hookCtx := pkg_plugin.HookPluginContext{Variables: initialCtx.Variables, OutputDirectory: initialCtx.OutputDirectory}
		for _, hookName := range cfg.Hooks {
			hookPlugin, ok := w.pluginManager.GetHook(hookName)
			if !ok {
				return fmt.Errorf("configured post-processing hook '%s' not found or loaded", hookName)
			}
			meta, _ := hookPlugin.GetMetadata()
			fmt.Printf("  Running hook: %s (Plugin: %s)\n", hookName, meta.Name)
			hookType := "PostGenerate"
			err := hookPlugin.Execute(hookType, hookCtx)
			if err != nil {
				return fmt.Errorf("hook '%s' (Plugin: %s) failed: %w", hookName, meta.Name, err)
			}
		}
		fmt.Println("Hook execution finished.")
	} else {
		fmt.Println("No post-processing hooks configured.")
	}

	return nil // Success
}
