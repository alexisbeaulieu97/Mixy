from mixy.plugins.plugin_base import PluginBase
from mixy.plugins.plugin_capability import PluginCapability
from mixy.plugins.unique_plugin_capability import UniquePluginCapability


class Plugin(PluginBase):
    @staticmethod
    def name() -> str:
        return "file"

    @staticmethod
    def category() -> str:
        return "parser"

    @staticmethod
    def capabilities() -> frozenset[PluginCapability]:
        """
        This should be overridden to return a list
        of capabilities that the plugin can handle.
        Each capability is a PluginCapability.
        """
        return frozenset(
            (
                PluginCapability(name="type", value="directory"),
                UniquePluginCapability(name="file_type", value=None),
            ),
        )

    def run(self, criteria_value) -> None:
        """
        This hook runs when a criteria needs to be processed.
        """
        ...
