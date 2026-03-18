"""Hookspecs for the Mixy plugin system."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pluggy

from mixy.application.ports import SourceProvider

if TYPE_CHECKING:
    pass

hookspec = pluggy.HookspecMarker("mixy")


class MixySpec:
    """Hookspecs for Mixy plugin extensions."""

    @hookspec
    def mixy_source_provider(self) -> SourceProvider | None:
        """Return a source provider to register, or None.

        All non-None results are collected and passed to SourceResolver.
        Implement this to add support for a new source type.
        """
