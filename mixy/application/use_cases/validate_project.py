"""Application use case for config validation."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import List

import yaml

from mixy.application.composition import build_config_loader
from mixy.application.ports import ConfigLoader
from mixy.domain.exceptions import ConfigValidationError
from mixy.domain.models import ProjectDefinition
from mixy.domain.services import ValidationIssue
from mixy.domain.services import validate as validate_definition

ValidationFn = Callable[[ProjectDefinition], List[ValidationIssue]]


def validate_project(
    config_path: Path,
    *,
    config_loader: ConfigLoader | None = None,
    config_validator: ValidationFn | None = None,
) -> list[ValidationIssue]:
    """Load and semantically validate a project config."""
    validator = config_validator or validate_definition
    try:
        definition = build_config_loader(config_loader)(config_path)
    except ConfigValidationError as error:
        return _issues_from_config_validation(error) + _raw_duplicate_source_id_issues(config_path)
    return validator(definition)


def _issues_from_config_validation(error: ConfigValidationError) -> list[ValidationIssue]:
    if error.details:
        return [
            ValidationIssue(
                severity="error",
                field_path=_detail_field_path(detail),
                message=_detail_message(detail),
                suggestion=error.suggestion,
            )
            for detail in error.details
        ]

    return [
        ValidationIssue(
            severity="error",
            field_path=error.field_path or "<root>",
            message=str(error.args[0]),
            suggestion=error.suggestion,
        )
    ]


def _detail_field_path(detail: str) -> str:
    field_path, _, _ = detail.partition(": ")
    return field_path or "<root>"


def _detail_message(detail: str) -> str:
    _, _, message = detail.partition(": ")
    return message or detail


def _raw_duplicate_source_id_issues(config_path: Path) -> list[ValidationIssue]:
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            raw_data = yaml.safe_load(handle) or {}
    except OSError:
        return []

    if not isinstance(raw_data, dict):
        return []

    raw_sources = raw_data.get("sources")
    if not isinstance(raw_sources, list):
        return []

    issues: list[ValidationIssue] = []
    seen_ids: set[str] = set()
    for index, source in enumerate(raw_sources):
        if not isinstance(source, dict):
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str):
            continue
        if source_id in seen_ids:
            issues.append(
                ValidationIssue(
                    severity="error",
                    field_path=f"sources[{index}].id",
                    message=f'Duplicate source id "{source_id}".',
                    suggestion="Use a unique id for each source entry.",
                )
            )
        seen_ids.add(source_id)

    return issues
