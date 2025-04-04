// Package resolver provides template loader resolution functionality.
package resolver

import (
	"fmt"
	"log/slog"
	"strings"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// pluginPrefix is the standard prefix for plugin type hints.
const pluginPrefix = "plugin:"

// BasicLoaderResolver implements LoaderResolver by iterating through available loaders
// to find one that supports the given template source. It handles both standard and
// plugin-based template sources through type hints.
type BasicLoaderResolver struct {
	// AvailableLoaders is the list of template loaders to try.
	// The order determines precedence when multiple loaders support the same source.
	AvailableLoaders []core.TemplateLoader
}

// NewBasicLoaderResolver creates a new BasicLoaderResolver with the given loaders.
//
// Parameters:
//   - loaders: Slice of TemplateLoader implementations to use for resolution
//
// Returns:
//   - core.LoaderResolver: The configured resolver
//
// Panics if loaders is empty, as at least one loader is required for operation.
func NewBasicLoaderResolver(loaders []core.TemplateLoader) core.LoaderResolver {
	if len(loaders) == 0 {
		panic("basic loader resolver requires at least one template loader")
	}

	// Create defensive copy of loaders slice
	resolverLoaders := make([]core.TemplateLoader, len(loaders))
	copy(resolverLoaders, loaders)

	return &BasicLoaderResolver{
		AvailableLoaders: resolverLoaders,
	}
}

// Resolve determines the appropriate loader and source string for a template.
// It handles special processing for plugin type hints and attempts to find
// a loader that supports the given source.
//
// Parameters:
//   - ts: The template source configuration to resolve
//   - logger: Logger for operation tracking
//
// Returns:
//   - loader: The resolved template loader (nil if none found)
//   - sourceForLoad: The processed source string to pass to the loader
//   - err: Error if resolution fails
func (r *BasicLoaderResolver) Resolve(ts core.TemplateSource, logger *slog.Logger) (loader core.TemplateLoader, sourceForLoad string, err error) {
	// Input validation
	if logger == nil {
		return nil, "", core.NewTemplateLoadError("nil logger provided", nil)
	}
	if ts.Source == "" {
		return nil, "", core.NewTemplateLoadError("empty source", nil)
	}

	// Setup logging
	resLogger := logger.With(
		slog.String("component", "loader_resolver"),
		slog.String("original_source", ts.Source),
		slog.String("type_hint", ts.Type))

	resLogger.Debug("Starting template loader resolution")

	// Initialize source references
	sourceToCheck := ts.Source
	sourceForLoad = ts.Source

	// Process type hint if present
	if ts.Type != "" {
		sourceToCheck, sourceForLoad, err = r.processTypeHint(ts, resLogger)
		if err != nil {
			return nil, "", err
		}
	}

	// Find supporting loader
	loader, err = r.findSupportingLoader(sourceToCheck, sourceForLoad, resLogger)
	if err != nil {
		return nil, "", err
	}

	resLogger.Info("Template loader resolution successful",
		slog.String("loader_type", fmt.Sprintf("%T", loader)),
		slog.String("load_source", sourceForLoad))

	return loader, sourceForLoad, nil
}

// processTypeHint handles the processing of template type hints, particularly
// for plugin-based templates. It returns the processed source strings for
// both checking support and loading.
func (r *BasicLoaderResolver) processTypeHint(ts core.TemplateSource, logger *slog.Logger) (checkSource, loadSource string, err error) {
	logger.Debug("Processing type hint", slog.String("type", ts.Type))

	// Handle plugin type hints
	if strings.HasPrefix(ts.Type, pluginPrefix) {
		parts := strings.SplitN(ts.Type, ":", 2)
		if len(parts) != 2 {
			return "", "", core.NewConfigurationError(
				fmt.Sprintf("invalid plugin type hint format '%s'", ts.Type),
				nil,
				slog.String("source", ts.Source))
		}

		pluginName := parts[1]
		if pluginName == "" {
			return "", "", core.NewConfigurationError(
				"empty plugin name in type hint",
				nil,
				slog.String("source", ts.Source))
		}

		constructedName := fmt.Sprintf("%s%s:%s", pluginPrefix, pluginName, ts.Source)
		logger.Debug("Constructed plugin source name",
			slog.String("name", constructedName))

		return constructedName, constructedName, nil
	}

	// Non-plugin type hints use original source
	logger.Debug("Using non-plugin type hint",
		slog.String("type", ts.Type))
	return ts.Source, ts.Source, nil
}

// findSupportingLoader attempts to find a loader that supports the given source.
// It returns the first supporting loader found, or an error if none is found.
func (r *BasicLoaderResolver) findSupportingLoader(sourceToCheck, sourceForLoad string, logger *slog.Logger) (core.TemplateLoader, error) {
	logger.Debug("Searching for supporting loader",
		slog.String("check_source", sourceToCheck))

	for _, currentLoader := range r.AvailableLoaders {
		loaderLogger := logger.With(
			slog.String("loader_type", fmt.Sprintf("%T", currentLoader)))

		if currentLoader.Supports(sourceToCheck) {
			loaderLogger.Debug("Found supporting loader")
			return currentLoader, nil
		}
		loaderLogger.Debug("Loader does not support source")
	}

	// No supporting loader found
	return nil, core.NewTemplateLoadError(
		"no suitable loader found",
		nil,
		slog.String("source", sourceToCheck),
		slog.String("load_source", sourceForLoad))
}
