"""Semantic validation for parsed Mixy project configs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from mixy.domain.models import (
    LocalDirSource,
    ProjectDefinition,
)

ValidationSeverity = str


@dataclass(frozen=True)
class ValidationIssue:
    severity: ValidationSeverity
    field_path: str
    message: str
    suggestion: str | None = None


def validate(definition: ProjectDefinition) -> List[ValidationIssue]:
    """Return semantic validation issues for a parsed project definition."""
    issues: List[ValidationIssue] = []
    seen_ids: set[str] = set()

    for index, source in enumerate(definition.sources):
        if source.id in seen_ids:
            issues.append(
                ValidationIssue(
                    severity="error",
                    field_path=f"sources[{index}].id",
                    message=f'Duplicate source id "{source.id}".',
                    suggestion="Use a unique id for each source entry.",
                )
            )
        seen_ids.add(source.id)

        if not source.enabled:
            continue

        if isinstance(source.source, LocalDirSource):
            _add_path_error(
                issues=issues,
                path=source.source.path,
                field_path=f"sources[{index}].source.path",
            )

    return issues


def _add_path_error(
    *,
    issues: list[ValidationIssue],
    path: Path,
    field_path: str,
) -> None:
    if path.exists():
        return
    issues.append(
        ValidationIssue(
            severity="error",
            field_path=field_path,
            message=f'Local source path "{path}" does not exist.',
            suggestion="Create the path or update the config reference.",
        )
    )
