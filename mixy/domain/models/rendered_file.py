"""Rendered file value object."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RenderedFile:
    output_name: str
    content: bytes
    rendered: bool
    is_binary: bool
    output_relative_path: Path | None = None
