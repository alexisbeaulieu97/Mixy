from typing import Type

from mixy.models.base import BaseModel
from mixy.plugins.plugin_base import PluginBase
from mixy.plugins.plugin_capability import PluginCapability
from mixy.plugins.unique_plugin_capability import UniquePluginCapability


class PluginManager(BaseModel):
    category: str
    plugins: set[Type[PluginBase]] = set()
    unique_capabilities: dict[PluginCapability, Type[PluginBase]] = {}

    def register_plugin(self, plugin: Type[PluginBase]) -> None:
        if plugin.category() != self.category:
            raise TypeError(f"Registered plugin must be of category {self.category}")

        for capability in plugin.capabilities():
            registered_plugin = self.unique_capabilities.get(capability, None)
            if registered_plugin is not None:
                raise ValueError(
                    f"Could not register capability for plugin {plugin.name()}. "
                    f"Unique capability {capability.name} has already "
                    f"been registered by plugin {registered_plugin.name()}."
                )
            if isinstance(capability, UniquePluginCapability):
                self.unique_capabilities[capability] = plugin
        self.plugins.add(plugin)

    def get_plugin(self, plugin_name: str) -> Type[PluginBase]:
        for plugin in self.plugins:
            if plugin.name() == plugin_name:
                return plugin
        raise ValueError(f"No plugin found with identifier {plugin_name}")

    def search_plugins(self, *criteria: PluginCapability) -> set[Type[PluginBase]]:
        matching = set()
        for plugin in self.plugins:
            if all(
                any(c.matches(criterion) for c in plugin.capabilities())
                for criterion in criteria
            ):
                matching.add(plugin)
        return matching

    def search_best_plugins(self, *criteria: PluginCapability) -> set[Type[PluginBase]]:
        best_matches: set[Type[PluginBase]] = set()
        min_wildcards = None

        for plugin in self.plugins:
            capabilities = plugin.capabilities()

            matches_all_criteria = all(
                any(c.matches(criterion) for c in capabilities)
                for criterion in criteria
            )
            if matches_all_criteria:
                num_wildcards = sum(
                    1
                    for c in capabilities
                    if c.value is None
                    and any(c.matches(criterion) for criterion in criteria)
                )

                if min_wildcards is None or num_wildcards < min_wildcards:
                    best_matches = {plugin}
                elif num_wildcards == min_wildcards:
                    best_matches.add(plugin)

        return best_matches
