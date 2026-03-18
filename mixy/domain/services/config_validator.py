"""Semantic validation for parsed Mixy project configs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from mixy.domain.enums import VariableType
from mixy.domain.models import (
    LocalDirSource,
    ProjectDefinition,
)

ValidationSeverity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    severity: ValidationSeverity
    field_path: str
    message: str
    suggestion: str | None = None


def validate(definition: ProjectDefinition) -> list[ValidationIssue]:
    """Return semantic validation issues for a parsed project definition."""
    issues: list[ValidationIssue] = []
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

        if isinstance(source.source, LocalDirSource):
            _add_path_error(
                issues=issues,
                path=source.source.path,
                field_path=f"sources[{index}].source.path",
            )

    for name, variable in definition.variables.items():
        if variable.default is not None and not _matches_variable_type(
            variable.type, variable.default
        ):
            issues.append(
                ValidationIssue(
                    severity="error",
                    field_path=f"variables.{name}.default",
                    message=(
                        f'Default value for variable "{name}" does not match type '
                        f'"{variable.type.value}".'
                    ),
                    suggestion="Update the default value or change the declared variable type.",
                )
            )

        if variable.choices is None:
            continue

        for choice_index, choice in enumerate(variable.choices):
            if _matches_variable_type(variable.type, choice):
                continue
            issues.append(
                ValidationIssue(
                    severity="error",
                    field_path=f"variables.{name}.choices[{choice_index}]",
                    message=(
                        f'Choice value for variable "{name}" does not match type '
                        f'"{variable.type.value}".'
                    ),
                    suggestion="Ensure every choice uses the declared variable type.",
                )
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


def _matches_variable_type(expected: VariableType, value: object) -> bool:
    if expected is VariableType.STR:
        return isinstance(value, str)
    if expected is VariableType.INT:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected is VariableType.FLOAT:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, bool)
