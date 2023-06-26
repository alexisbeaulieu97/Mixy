import importlib.util
import pkgutil
from abc import ABCMeta
from pathlib import Path
from types import ModuleType
from typing import Type

from mixy.plugins.plugin_base import PluginBase
from mixy.plugins.plugin_capability import PluginCapability
from mixy.plugins.plugin_manager import PluginManager
from mixy.settings.settings import settings


class PluginLoader:
    SYSTEM_PLUGIN_PACKAGES = ["mixy.plugins.handlers", "mixy.plugins.parsers"]

    def __init__(self) -> None:
        self.managers: dict[str, PluginManager] = {}
        self._load_user_plugins()
        self._load_system_plugins()
        print(self.managers)
        print()

    def _load_user_plugins(self) -> None:
        if not settings.plugins.location.exists():
            return
        for plugin_settings in settings.plugins.plugins:
            if not plugin_settings.active:
                continue
            plugin_location = settings.plugins.location.joinpath(
                plugin_settings.location
            )
            plugin = self.get_plugin_from_file(plugin_location)
            if plugin is not None:
                self.register_plugin(plugin)

    def _load_system_plugins(self) -> None:
        for system_plugin_package in self.SYSTEM_PLUGIN_PACKAGES:
            plugins = self.get_plugins_from_package(system_plugin_package)
            for plugin in plugins:
                self.register_plugin(plugin)

    def get_plugin_from_module(self, module: ModuleType) -> Type[PluginBase] | None:
        plugin = getattr(module, "Plugin", None)
        if (
            isinstance(plugin, type)
            and issubclass(plugin, PluginBase)
            and not (isinstance(plugin, ABCMeta) and plugin.__abstractmethods__)
        ):
            return plugin
        return None

    def get_module_from_file(self, plugin_file: Path) -> ModuleType:
        if plugin_file.suffix != ".py":
            raise ImportError(f"The file {plugin_file} is not a Python plugin file")

        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)

        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load plugin from file {plugin_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def get_plugin_from_file(self, plugin_file: Path) -> Type[PluginBase] | None:
        module = self.get_module_from_file(plugin_file)
        return self.get_plugin_from_module(module)

    def get_module_from_package(
        self, package_name: str, module_name: str
    ) -> ModuleType:
        full_module_name = f"{package_name}.{module_name}"
        module = importlib.import_module(full_module_name)
        return module

    def get_plugins_from_package(self, package_name: str) -> list[Type[PluginBase]]:
        package = importlib.import_module(package_name)
        plugins: list[Type[PluginBase]] = []
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            module = self.get_module_from_package(package_name, module_name)
            plugin = self.get_plugin_from_module(module)
            if plugin is not None:
                plugins.append(plugin)
        return plugins

    def register_plugin(self, plugin: Type[PluginBase]) -> None:
        category = plugin.category()
        if category not in self.managers:
            self.managers[category] = PluginManager(category=category)
        manager = self.managers[category]
        manager.register_plugin(plugin)

    def search_plugins(
        self, category: str, *criteria: PluginCapability
    ) -> set[Type[PluginBase]] | None:
        """
        Get the plugins that can handle the given criteria in the given category.
        """
        manager = self.managers.get(category, None)
        if manager is None:
            return None
        return manager.search_plugins(*criteria)

    def search_best_plugins(
        self, category: str, *criteria: PluginCapability
    ) -> set[Type[PluginBase]] | None:
        """
        Get the plugins that can handle the given criteria in the given category.
        """
        manager = self.managers.get(category, None)
        if manager is None:
            return None
        return manager.search_best_plugins(*criteria)


plugin_loader = PluginLoader()
