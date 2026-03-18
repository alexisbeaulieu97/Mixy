"""Local filesystem source providers."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from mixy.domain.exceptions import SourceResolutionError
from mixy.domain.models import LocalDirSource, MaterializedSource, SourceDefinition


class LocalDirProvider:
    """Resolve `local_dir` sources into local directory trees."""

    def can_handle(self, source: SourceDefinition) -> bool:
        return source.type == "local_dir"

    def resolve(self, source: SourceDefinition) -> MaterializedSource:
        if not isinstance(source, LocalDirSource):
            raise SourceResolutionError(
                f'LocalDirProvider cannot resolve source type "{source.type}".',
                suggestion="Use a `local_dir` source with a directory path.",
            )

        root_path = source.path.expanduser().resolve()
        if source.subpath:
            root_path = (root_path / source.subpath).resolve()

        if not root_path.exists():
            raise SourceResolutionError(
                f'Local directory source path does not exist: "{root_path}".',
                suggestion="Create the directory or update the configured source path.",
            )
        if not root_path.is_dir():
            raise SourceResolutionError(
                f'Local directory source path must be a directory: "{root_path}".',
                suggestion="Point the source to a directory instead of a file.",
            )

        return MaterializedSource(
            root_path=root_path,
            source_id=_default_source_id(root_path),
            fingerprint=self.fingerprint(source),
            metadata={"provider": "local_dir"},
        )

    def fingerprint(self, source: SourceDefinition) -> str:
        if not isinstance(source, LocalDirSource):
            raise SourceResolutionError(
                f'LocalDirProvider cannot fingerprint source type "{source.type}".',
                suggestion="Use a `local_dir` source with a directory path.",
            )

        root_path = source.path.expanduser().resolve()
        if source.subpath:
            root_path = (root_path / source.subpath).resolve()

        stat = root_path.stat()
        payload = f"{root_path}:{stat.st_mtime_ns}".encode()
        return sha256(payload).hexdigest()


def _default_source_id(path: Path) -> str:
    return path.name or path.as_posix()
