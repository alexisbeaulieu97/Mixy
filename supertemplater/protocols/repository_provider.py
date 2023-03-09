from pathlib import Path
from typing import Protocol, Self


class RepositoryProvider(Protocol):
    @property
    def location(self) -> Path | None:
        ...

    @classmethod
    def cache_or_clone(cls, url: str, dest: Path) -> Self:
        ...

    def is_branch_behind(self, branch: str) -> bool:
        ...

    def checkout(self, version: str) -> None:
        ...

    def fetch(self, tags: bool = True) -> None:
        ...

    def pull(self, tags: bool = True) -> None:
        ...

    def update(self) -> None:
        ...
