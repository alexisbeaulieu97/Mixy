from pathlib import Path
from typing import Protocol, runtime_checkable

from mixy.context import Context


@runtime_checkable
class Dependency(Protocol):
    def resolve(self, into_dir: Path, context: Context) -> None:
        ...
