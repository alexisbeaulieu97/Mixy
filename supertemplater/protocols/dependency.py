from pathlib import Path
from typing import Protocol

from supertemplater.context import Context


class Dependency(Protocol):
    def resolve(self, into_dir: Path, context: Context) -> None:
        ...
