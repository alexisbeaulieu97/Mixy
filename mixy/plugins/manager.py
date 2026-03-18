"""Plugin manager factory for Mixy."""

from __future__ import annotations

import pluggy

from mixy.application.ports import SourceProvider
from mixy.plugins.builtin import BUILTIN_PLUGINS
from mixy.plugins.hookspecs import MixySpec


def create_manager() -> pluggy.PluginManager:
    """Create a PluginManager with built-in plugins and any installed entry-point plugins."""
    pm = pluggy.PluginManager("mixy")
    pm.add_hookspecs(MixySpec)

    for plugin in BUILTIN_PLUGINS:
        pm.register(plugin)

    pm.load_setuptools_entrypoints("mixy")
    return pm


def get_source_providers(pm: pluggy.PluginManager | None = None) -> list[SourceProvider]:
    """Return all registered source providers, in registration order."""
    manager = pm or create_manager()
    results: list[SourceProvider | None] = manager.hook.mixy_source_provider()
    return [p for p in results if p is not None]
