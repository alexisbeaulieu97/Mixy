"""YAML config loader for Mixy project definitions."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from mixy.domain.exceptions import ConfigValidationError, UnsupportedVersionError
from mixy.domain.models import ProjectDefinition

SUPPORTED_CONFIG_VERSION = "1"


def load_config(path: Path) -> ProjectDefinition:
    """Load a YAML config file into a validated project definition."""
    config_path = path.expanduser().resolve()
    raw_data = _load_yaml(config_path)

    version = raw_data.get("version")
    if version is None:
        raise ConfigValidationError(
            "Config version is required.",
            field_path="version",
            suggestion='Add `version: "1"` at the top of the config file.',
        )
    if version != SUPPORTED_CONFIG_VERSION:
        raise UnsupportedVersionError(str(version), supported_version=SUPPORTED_CONFIG_VERSION)

    resolved_data = _resolve_relative_paths(raw_data, config_path.parent)

    try:
        return ProjectDefinition.model_validate(resolved_data)
    except ValidationError as error:
        raise _to_config_validation_error(error) from error


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if isinstance(data, dict):
        return data

    raise ConfigValidationError(
        "Config file must contain a YAML mapping at the top level.",
        field_path="<root>",
        suggestion="Replace the top-level YAML value with a mapping of config keys and values.",
    )


def _resolve_relative_paths(data: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    resolved = deepcopy(data)

    for source_entry in resolved.get("sources", []):
        if not isinstance(source_entry, dict):
            continue
        source = source_entry.get("source")
        if not isinstance(source, dict):
            continue
        if source.get("type") != "local_dir":
            continue

        path_value = source.get("path")
        if isinstance(path_value, str):
            source["path"] = str(_resolve_path(path_value, base_dir))

    output = resolved.get("output")
    if isinstance(output, dict):
        output_path = output.get("path")
        if isinstance(output_path, str):
            output["path"] = str(_resolve_path(output_path, base_dir))

    return resolved


def _resolve_path(value: str, base_dir: Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _to_config_validation_error(error: ValidationError) -> ConfigValidationError:
    first = error.errors(include_url=False)[0]
    field_path = _format_field_path(first["loc"])
    message = str(first["msg"])
    suggestion = _suggestion_for(field_path)
    return ConfigValidationError(message, field_path=field_path, suggestion=suggestion)


def _format_field_path(location: tuple[Any, ...]) -> str:
    path = ""
    for item in location:
        if isinstance(item, int):
            path += f"[{item}]"
        else:
            if path and not path.endswith("]"):
                path += "."
            elif path and path.endswith("]"):
                path += "."
            path += str(item)
    return path or "<root>"


def _suggestion_for(field_path: str) -> str:
    if field_path == "version":
        return 'Add `version: "1"` at the top of the config file.'
    if field_path.endswith(".type") or field_path == "type":
        return "Use one of the supported source types: local_dir, git."
    return "Check the YAML field path and ensure the value matches the expected schema."
