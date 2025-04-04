// internal/workflow/resolver/loader_resolver.go
package resolver

import (
	"fmt"
	"log/slog"
	"strings"

	"github.com/alexisbeaulieu97/Mixy/internal/core"
)

// BasicLoaderResolver iterates through available loaders to find one supporting the source.
type BasicLoaderResolver struct {
	AvailableLoaders []core.TemplateLoader
}

// NewBasicLoaderResolver creates a resolver.
func NewBasicLoaderResolver(loaders []core.TemplateLoader) core.LoaderResolver {
	if len(loaders) == 0 {
		panic("BasicLoaderResolver requires at least one TemplateLoader")
	}
	return &BasicLoaderResolver{AvailableLoaders: loaders}
}

// Resolve determines the appropriate loader and the source string to pass to its Load method.
func (r *BasicLoaderResolver) Resolve(ts core.TemplateSource, logger *slog.Logger) (loader core.TemplateLoader, sourceForLoad string, err error) {
	resLogger := logger.With(slog.String("component", "loader_resolver"), slog.String("original_source", ts.Source), slog.String("type_hint", ts.Type))
	resLogger.Debug("Attempting to resolve template loader")

	sourceToCheck := ts.Source // Default source for Supports() check
	sourceForLoad = ts.Source  // Default source for Load() call

	// Handle type hint, modifying check/load sources if it's a plugin hint
	if ts.Type != "" {
		resLogger.Debug("Processing type hint")
		if strings.HasPrefix(ts.Type, "plugin:") {
			parts := strings.SplitN(ts.Type, ":", 2)
			if len(parts) == 2 {
				pluginName := parts[1]
				constructedName := fmt.Sprintf("plugin:%s:%s", pluginName, ts.Source)
				sourceToCheck = constructedName
				sourceForLoad = constructedName // Use constructed name for Load too
				resLogger.Debug("Constructed plugin source name", slog.String("name", sourceToCheck))
			} else {
				resLogger.Error("Invalid plugin type hint format")
				err = core.NewConfigurationError(fmt.Sprintf("invalid plugin type hint format '%s' for source '%s'", ts.Type, ts.Source), nil)
				return // Return error
			}
		} else {
			resLogger.Debug("Non-plugin type hint found (informational)", slog.String("type", ts.Type))
		}
	} else {
		resLogger.Debug("No type hint provided")
	}

	// Find a supporting loader
	for _, currentLoader := range r.AvailableLoaders {
		loaderLogger := resLogger.With(slog.String("loader_type", fmt.Sprintf("%T", currentLoader)), slog.String("check_source", sourceToCheck))
		if currentLoader.Supports(sourceToCheck) {
			loaderLogger.Debug("Loader supports source")
			loader = currentLoader // Found loader
			// sourceForLoad was already set correctly above
			resLogger.Info("Resolved template loader successfully", slog.String("loader_type", fmt.Sprintf("%T", loader)), slog.String("load_source", sourceForLoad))
			return // Return found loader and source
		} else {
			loaderLogger.Debug("Loader does not support source")
		}
	}

	// No loader found
	resLogger.Error("No suitable loader found for template source")
	err = core.NewTemplateLoadError("no suitable loader found", nil, slog.String("source", ts.Source), slog.String("type_hint", ts.Type), slog.String("checked_source", sourceToCheck))
	return // Return nil loader and the error
}
