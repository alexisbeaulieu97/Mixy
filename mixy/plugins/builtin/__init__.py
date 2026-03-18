"""Built-in plugin implementations for Mixy."""

from __future__ import annotations

import pluggy

from mixy.application.ports import SourceProvider
from mixy.infrastructure.sources.git import GitSourceProvider
from mixy.infrastructure.sources.local import LocalDirProvider

hookimpl = pluggy.HookimplMarker("mixy")


class _LocalDirPlugin:
    @hookimpl
    def mixy_source_provider(self) -> SourceProvider:
        return LocalDirProvider()


class _GitPlugin:
    @hookimpl
    def mixy_source_provider(self) -> SourceProvider:
        return GitSourceProvider()


BUILTIN_PLUGINS: list[object] = [_LocalDirPlugin(), _GitPlugin()]
