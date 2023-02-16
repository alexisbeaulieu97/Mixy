from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class Updatable(Protocol):
    def update(self, data: Self) -> None:
        ...
