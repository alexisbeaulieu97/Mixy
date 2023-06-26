from mixy.plugins.plugin_capability import PluginCapability


class UniquePluginCapability(PluginCapability):
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PluginCapability):
            return NotImplemented
        return self.name == other.name and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.name, self.value))
