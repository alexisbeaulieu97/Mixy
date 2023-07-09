from types import ModuleType

import pluggy

from mixy.constants import PLUGIN_PROJECT_NAME
from mixy.modutil import get_modules_in_package
from mixy.plugins import builtin, hookspecs


class PluginManager(pluggy.PluginManager):
    def register_package_plugins(self, package: ModuleType) -> None:
        modules = get_modules_in_package(package)
        for plugin in modules:
            self.register(plugin)


plugin_master = PluginManager(PLUGIN_PROJECT_NAME)
plugin_master.add_hookspecs(hookspecs)
plugin_master.register_package_plugins(builtin)
