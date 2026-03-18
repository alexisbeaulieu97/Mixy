"""Internal shared pre-merge planning artifact."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mixy.domain.models.rendered_file import RenderedFile


@dataclass(frozen=True, slots=True)
class PreMergeEntry:
    source_id: str
    source_path: Path
    relative_path: Path
    output_relative_path: Path
    rendered_file: RenderedFile


@dataclass(frozen=True, slots=True)
class PreMergeArtifact:
    directory_paths: dict[Path, list[str]]
    file_entries: list[PreMergeEntry]
