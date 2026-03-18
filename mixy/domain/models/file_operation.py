"""Planned filesystem operations for generated output."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from mixy.domain.models.rendered_file import RenderedFile


@dataclass(frozen=True, slots=True)
class CreateDir:
    path: Path


@dataclass(frozen=True, slots=True)
class CopyRaw:
    source_path: Path
    output_path: Path
    source_id: str
    rendered_file: RenderedFile


@dataclass(frozen=True, slots=True)
class RenderTemplate:
    source_path: Path
    output_path: Path
    source_id: str
    rendered_file: RenderedFile


@dataclass(frozen=True, slots=True)
class SkipExisting:
    source_path: Path
    output_path: Path
    source_id: str
    existing_source_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class Overwrite:
    source_path: Path
    output_path: Path
    source_id: str
    previous_source_id: str
    rendered_file: RenderedFile


FileOperation: TypeAlias = CreateDir | CopyRaw | RenderTemplate | SkipExisting | Overwrite
