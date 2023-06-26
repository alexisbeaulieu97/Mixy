from abc import ABC, abstractmethod

from mixy.plugins.plugin_capability import PluginCapability


class PluginBase(ABC):
    @staticmethod
    @abstractmethod
    def name() -> str:
        ...

    @staticmethod
    @abstractmethod
    def category() -> str:
        ...

    @staticmethod
    @abstractmethod
    def capabilities() -> list[PluginCapability]:
        """
        This should be overridden to return a list of capabilities that the plugin can handle.
        Each capability is a tuple (criteria_type, criteria_value).
        """
        ...

    def pre_run(self, criteria_value) -> None:
        """
        This hook runs before a criteria has been processed.
        """
        ...

    @abstractmethod
    def run(self, criteria_value) -> None:
        """
        This hook runs when a criteria needs to be processed.
        """
        ...

    def post_run(self, criteria_value) -> None:
        """
        This hook runs after a criteria has been processed.
        """
        ...
