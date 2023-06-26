from typing import Any, Self
from mixy.models.base import BaseModel


class PluginCapability(BaseModel):
    name: str
    value: Any

    def matches(self, other: Self) -> bool:
        return self.name == other.name and (
            self.value == other.value or self.value is None or other.value is None
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PluginCapability):
            return NotImplemented
        return self.name == other.name and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.name, self.value))
