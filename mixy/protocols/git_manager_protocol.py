from pathlib import Path
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class GitManagerProtocol(Protocol):
    @property
    def location(self) -> Path | None:
        ...

    @classmethod
    def cache_or_clone(cls, url: str, dest: Path) -> Self:
        ...

    def pull(self):
        ...

    def checkout(self, version: str):
        ...
