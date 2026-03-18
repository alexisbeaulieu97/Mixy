"""Recursive template metadata discovery and parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from mixy.domain.exceptions import MetadataValidationError
from mixy.domain.models import TemplateMetadata

DIRECTORY_METADATA_DIR = ".mixy"
DIRECTORY_METADATA_FILE = "template.yml"
FILE_METADATA_SUFFIX = ".mixy.yml"


@dataclass(frozen=True, slots=True)
class DiscoveredMetadata:
    directory_scopes: dict[Path, TemplateMetadata] = field(default_factory=dict)
    file_scopes: dict[Path, TemplateMetadata] = field(default_factory=dict)


class MetadataLoader:
    """Discover and parse template metadata files from a materialized source tree."""

    def discover(self, source_root: Path) -> DiscoveredMetadata:
        root = source_root.expanduser().resolve()
        directory_scopes: dict[Path, TemplateMetadata] = {}
        file_scopes: dict[Path, TemplateMetadata] = {}

        for directory in sorted([root, *[path for path in root.rglob("*") if path.is_dir()]]):
            metadata_path = directory / DIRECTORY_METADATA_DIR / DIRECTORY_METADATA_FILE
            if metadata_path.is_file():
                directory_scopes[self._relative_directory(directory, root)] = self._load_metadata(
                    metadata_path
                )

        for metadata_path in sorted(root.rglob(f"*{FILE_METADATA_SUFFIX}")):
            if not metadata_path.is_file():
                continue

            target_path = metadata_path.with_name(metadata_path.name[: -len(FILE_METADATA_SUFFIX)])
            if not target_path.is_file():
                raise MetadataValidationError(
                    "Metadata sidecar must target an existing file.",
                    file_path=str(metadata_path),
                )

            file_scopes[target_path.relative_to(root)] = self._load_metadata(metadata_path)

        return DiscoveredMetadata(
            directory_scopes=directory_scopes,
            file_scopes=file_scopes,
        )

    def _load_metadata(self, path: Path) -> TemplateMetadata:
        raw_data = self._load_yaml(path)

        try:
            return TemplateMetadata.model_validate(raw_data)
        except ValidationError as error:
            first = error.errors(include_url=False)[0]
            field_path = ".".join(str(part) for part in first["loc"]) or None
            raise MetadataValidationError(
                str(first["msg"]),
                file_path=str(path),
                field_path=field_path,
            ) from error

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

        if isinstance(data, dict):
            return data

        raise MetadataValidationError(
            "Metadata file must contain a YAML mapping at the top level.",
            file_path=str(path),
            field_path="<root>",
        )

    @staticmethod
    def _relative_directory(directory: Path, source_root: Path) -> Path:
        relative = directory.relative_to(source_root)
        if not relative.parts:
            return Path(".")
        return relative
