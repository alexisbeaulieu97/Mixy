"""Render plan aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mixy.domain.enums import ConflictPolicy
from mixy.domain.models.conflict import Conflict
from mixy.domain.models.file_operation import (
    CopyRaw,
    CreateDir,
    FileOperation,
    Overwrite,
    RenderTemplate,
    SkipExisting,
)


@dataclass(frozen=True, slots=True)
class RenderPlan:
    operations: list[FileOperation]
    conflicts: list[Conflict]
    conflict_policy: ConflictPolicy
    output_path: Path

    def list_output_paths(self) -> list[Path]:
        paths: list[Path] = []
        for operation in self.operations:
            if isinstance(operation, CreateDir):
                paths.append(operation.path)
            elif isinstance(operation, (CopyRaw, RenderTemplate, SkipExisting, Overwrite)):
                paths.append(operation.output_path)
        return paths
