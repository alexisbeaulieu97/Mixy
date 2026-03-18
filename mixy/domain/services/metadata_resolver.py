"""Resolve effective template metadata for files within a source tree."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from mixy.domain.exceptions import MetadataConflictError
from mixy.domain.models import (
    EffectiveMetadata,
    MetadataPatternList,
    RenderMetadata,
    ScalarValue,
    TemplateMetadata,
    VariableDefinition,
)

METADATA_DIRECTORY_NAME = ".mixy"
METADATA_FILE_SUFFIX = ".mixy.yml"


def is_metadata_path(relative_path: Path) -> bool:
    """Return True when the relative path points to metadata, not template content."""

    return METADATA_DIRECTORY_NAME in relative_path.parts or relative_path.name.endswith(
        METADATA_FILE_SUFFIX
    )


class MetadataResolver:
    """Resolve inherited template metadata scopes for a given file."""

    def __init__(
        self,
        directory_scopes: Mapping[Path, TemplateMetadata] | None = None,
        file_scopes: Mapping[Path, TemplateMetadata] | None = None,
    ) -> None:
        self._directory_scopes = {
            self._normalize_scope(path): metadata
            for path, metadata in (directory_scopes or {}).items()
        }
        self._file_scopes = {
            self._normalize_scope(path): metadata for path, metadata in (file_scopes or {}).items()
        }

    def resolve_for_file(
        self,
        file_path: Path,
        source_root: Path,
        project_defaults: TemplateMetadata,
    ) -> EffectiveMetadata:
        relative = self._relative_file_path(file_path, source_root)
        scopes = [("project", project_defaults)]

        root_scope = self._directory_scopes.get(Path("."))
        if root_scope is not None:
            scopes.append((Path(".").as_posix(), root_scope))

        for directory in self._ancestor_directories(relative):
            metadata = self._directory_scopes.get(directory)
            if metadata is not None:
                scopes.append((directory.as_posix(), metadata))

        file_scope = self._file_scopes.get(relative)
        if file_scope is not None:
            scopes.append((relative.as_posix(), file_scope))

        effective = EffectiveMetadata()
        for scope_name, metadata in scopes:
            effective = self._merge_metadata(effective, metadata, scope_name=scope_name)

        return effective

    @classmethod
    def _merge_metadata(
        cls,
        current: EffectiveMetadata,
        incoming: TemplateMetadata,
        *,
        scope_name: str,
    ) -> EffectiveMetadata:
        updated = current.model_copy(deep=True)

        if "description" in incoming.model_fields_set and incoming.description is not None:
            updated.description = incoming.description

        if "copy_mode" in incoming.model_fields_set and incoming.copy_mode is not None:
            updated.copy_mode = incoming.copy_mode

        if "render" in incoming.model_fields_set and incoming.render is not None:
            updated.render = cls._merge_render(updated.render, incoming.render)

        if "include" in incoming.model_fields_set and incoming.include is not None:
            updated.include = cls._merge_pattern_list(updated.include, incoming.include)

        if "exclude" in incoming.model_fields_set and incoming.exclude is not None:
            updated.exclude = cls._merge_pattern_list(updated.exclude, incoming.exclude)

        if "defaults" in incoming.model_fields_set:
            updated.defaults = {
                **updated.defaults,
                **incoming.defaults,
            }

        if "variables" in incoming.model_fields_set:
            merged_variables = dict(updated.variables)
            for name, definition in incoming.variables.items():
                parent = merged_variables.get(name)
                if parent is None:
                    merged_variables[name] = definition
                    continue
                merged_variables[name] = cls._merge_variable_definition(
                    name=name,
                    parent=parent,
                    child=definition,
                    child_scope=scope_name,
                )
            updated.variables = merged_variables

        return updated

    @staticmethod
    def _merge_render(current: RenderMetadata, incoming: RenderMetadata) -> RenderMetadata:
        data = current.model_dump()
        for field in incoming.model_fields_set:
            value = getattr(incoming, field)
            if value is not None:
                data[field] = value
        return RenderMetadata.model_validate(data)

    @staticmethod
    def _merge_pattern_list(
        current: list[str],
        incoming: MetadataPatternList,
    ) -> list[str]:
        items = list(incoming.items)
        if incoming.replace:
            return items

        merged: list[str] = list(current)
        for item in items:
            if item not in merged:
                merged.append(item)
        return merged

    @classmethod
    def _merge_variable_definition(
        cls,
        *,
        name: str,
        parent: VariableDefinition,
        child: VariableDefinition,
        child_scope: str,
    ) -> VariableDefinition:
        if child.type != parent.type:
            raise cls._conflict(
                name,
                child_scope,
                (
                    f'Variable "{name}" cannot change type from "{parent.type.value}" '
                    f'to "{child.type.value}".'
                ),
            )

        if "secret" in child.model_fields_set and child.secret != parent.secret:
            raise cls._conflict(
                name,
                child_scope,
                f'Variable "{name}" cannot change secret from {parent.secret} to {child.secret}.',
            )

        if "required" in child.model_fields_set and not parent.required and child.required:
            raise cls._conflict(
                name,
                child_scope,
                f'Variable "{name}" cannot change required from false to true.',
            )

        if (
            "choices" in child.model_fields_set
            and child.choices is not None
            and parent.choices is not None
        ):
            parent_choices = set(parent.choices)
            child_choices = set(child.choices)
            if not child_choices.issubset(parent_choices):
                raise cls._conflict(
                    name,
                    child_scope,
                    (
                        f'Variable "{name}" choices {sorted(child_choices)!r} must be '
                        f"a subset of parent choices {sorted(parent_choices)!r}."
                    ),
                )

        merged = parent.model_dump()

        for field in child.model_fields_set:
            value = getattr(child, field)
            if field in {"type", "secret"}:
                continue
            if value is None:
                continue
            if field == "examples" and parent.examples is not None:
                merged[field] = _unique(parent.examples + value)
                continue
            merged[field] = value

        return VariableDefinition.model_validate(merged)

    @staticmethod
    def _conflict(name: str, child_scope: str, message: str) -> MetadataConflictError:
        return MetadataConflictError(
            message,
            variable_name=name,
            parent_scope="parent",
            child_scope=child_scope,
        )

    @staticmethod
    def _ancestor_directories(relative_path: Path) -> list[Path]:
        if relative_path.parent == Path("."):
            return []

        parts = relative_path.parent.parts
        return [Path(*parts[:index]) for index in range(1, len(parts) + 1)]

    @staticmethod
    def _normalize_scope(path: Path) -> Path:
        if not path.parts or path == Path("."):
            return Path(".")
        return Path(*path.parts)

    @staticmethod
    def _relative_file_path(file_path: Path, source_root: Path) -> Path:
        if file_path.is_absolute():
            return file_path.relative_to(source_root)
        return file_path


def _unique(items: list[ScalarValue]) -> list[ScalarValue]:
    ordered: list[ScalarValue] = []
    for item in items:
        if item not in ordered:
            ordered.append(item)
    return ordered
