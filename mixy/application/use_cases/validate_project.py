"""Application use case for config validation."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from mixy.application.composition import build_config_loader
from mixy.application.ports import ConfigLoader
from mixy.domain.models import ProjectDefinition
from mixy.domain.services import ValidationIssue, validate as validate_definition

ValidationFn = Callable[[ProjectDefinition], list[ValidationIssue]]


def validate_project(
    config_path: Path,
    *,
    config_loader: ConfigLoader | None = None,
    config_validator: ValidationFn | None = None,
) -> list[ValidationIssue]:
    """Load and semantically validate a project config."""
    validator = config_validator or validate_definition
    definition = build_config_loader(config_loader)(config_path)
    return validator(definition)
