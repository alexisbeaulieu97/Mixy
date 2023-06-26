from mixy.plugins.plugin_base import PluginBase
from mixy.plugins.plugin_capability import PluginCapability
from mixy.plugins.unique_plugin_capability import UniquePluginCapability


class Plugin(PluginBase):
    @staticmethod
    def name() -> str:
        return "directory"

    @staticmethod
    def category() -> str:
        return "parser"

    @staticmethod
    def capabilities() -> frozenset[PluginCapability]:
        """
        This should be overridden to return a list of capabilities that the plugin can handle.
        Each capability is a tuple (criteria_type, criteria_value).
        """
        return frozenset(
            (
                PluginCapability(name="type", value="directory"),
                PluginCapability(name="file_type", value=".mixy"),
            ),
        )

    def run(self, criteria_value) -> None:
        """
        This hook runs when a criteria needs to be processed.
        """
        ...
