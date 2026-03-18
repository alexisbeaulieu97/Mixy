"""Template-local metadata models and helpers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mixy.domain.models.config import ScalarValue, VariableDefinition

DISALLOWED_TEMPLATE_METADATA_FIELDS = frozenset(
    {"source", "output", "cache", "merge_strategy", "hooks", "imports"}
)

CopyMode = Literal["render", "raw"]
UndefinedPolicy = Literal["strict"]


class MetadataModel(BaseModel):
    """Base model for template metadata with strict schema handling."""

    model_config = ConfigDict(extra="forbid")


class RenderMetadata(MetadataModel):
    undefined: UndefinedPolicy | None = None
    path_names: bool | None = None
    text_files: bool | None = None


class MetadataPatternList(MetadataModel):
    items: list[str] = Field(default_factory=list)
    replace: bool = False

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: object) -> object:
        if isinstance(data, list):
            return {"items": data}
        if isinstance(data, tuple):
            return {"items": list(data)}
        if isinstance(data, Mapping):
            if "items" in data:
                return {"items": data.get("items", []), "replace": data.get("_replace", False)}
            allowed = {"_replace"}
            dynamic_items = [key for key in data if key not in allowed]
            if dynamic_items:
                raise ValueError(
                    "List metadata mappings must use `items` and optional `_replace` keys."
                )
            return {"items": [], "replace": data.get("_replace", False)}
        return data


class TemplateMetadata(MetadataModel):
    description: str | None = None
    copy_mode: CopyMode | None = None
    render: RenderMetadata | None = None
    include: MetadataPatternList | None = None
    exclude: MetadataPatternList | None = None
    defaults: dict[str, ScalarValue] = Field(default_factory=dict)
    variables: dict[str, VariableDefinition] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _reject_disallowed_fields(cls, data: object) -> object:
        if not isinstance(data, Mapping):
            return data

        disallowed = sorted(DISALLOWED_TEMPLATE_METADATA_FIELDS.intersection(data))
        if disallowed:
            field_names = ", ".join(disallowed)
            raise ValueError(f"Disallowed metadata field(s): {field_names}.")

        return data


class EffectiveMetadata(MetadataModel):
    description: str | None = None
    copy_mode: CopyMode | None = None
    render: RenderMetadata = Field(default_factory=RenderMetadata)
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)
    defaults: dict[str, ScalarValue] = Field(default_factory=dict)
    variables: dict[str, VariableDefinition] = Field(default_factory=dict)

    @property
    def render_paths(self) -> bool:
        return self.render.path_names is not False

    @property
    def render_text_files(self) -> bool:
        return self.render.text_files is not False

    @property
    def render_policy(self) -> dict[str, list[str]]:
        return {"include": list(self.include), "exclude": list(self.exclude)}

    def output_relative_path(self, source_relative_path: Path, rendered_name: str) -> Path:
        if not source_relative_path.parts:
            return Path(rendered_name)

        rendered_parts = list(source_relative_path.parts[:-1])
        rendered_parts.append(rendered_name)
        return Path(*rendered_parts)
