"""Application-owned rendering adapter contract."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


class RenderingAdapterError(Exception):
    """Low-level rendering failure surfaced through the application adapter seam."""

    def __init__(self, reason: str, *, variable_name: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.variable_name = variable_name


@runtime_checkable
class RenderingAdapter(Protocol):
    def is_binary(self, source_path: Path) -> bool:
        """Return True when the source path should be treated as binary."""

    def strip_jinja_suffix(self, name: str) -> str:
        """Return the path segment without the Jinja suffix."""

    def has_jinja_suffix(self, name: str) -> bool:
        """Return True when the path segment forces template rendering."""

    def render_string(self, template: str, context: Mapping[str, Any]) -> str:
        """Render a template string or raise `RenderingAdapterError`."""
