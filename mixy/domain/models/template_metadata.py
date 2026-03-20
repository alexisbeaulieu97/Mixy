"""Template-local metadata models and helpers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

from pydantic import BaseModel, Field, root_validator, validator

from mixy.domain.enums import CopyMode
from mixy.domain.models.config import ScalarValue, VariableDefinition

DISALLOWED_TEMPLATE_METADATA_FIELDS = frozenset(
    {"source", "output", "cache", "merge_strategy", "hooks", "imports"}
)
MetadataModelT = TypeVar("MetadataModelT", bound="MetadataModel")


class MetadataModel(BaseModel):
    """Base model for template metadata with strict schema handling."""

    class Config:
        extra = "forbid"

    @classmethod
    def model_validate(cls: Type[MetadataModelT], data: Any) -> MetadataModelT:
        return cls.parse_obj(data)

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return self.dict(**kwargs)

    def model_copy(self: MetadataModelT, **kwargs: Any) -> MetadataModelT:
        return self.copy(**kwargs)

    @classmethod
    def model_construct(cls: Type[MetadataModelT], **values: Any) -> MetadataModelT:
        return cls.construct(**values)

    @property
    def model_fields_set(self) -> Set[str]:
        return set(self.__fields_set__)


class RenderMetadata(MetadataModel):
    path_names: Optional[bool] = None
    text_files: Optional[bool] = None


class MetadataPatternList(MetadataModel):
    items: List[str] = Field(default_factory=list)
    replace: bool = False

    @staticmethod
    def normalize_data(data: Any) -> Any:
        if isinstance(data, list):
            return {"items": data}
        if isinstance(data, tuple):
            return {"items": list(data)}
        if isinstance(data, Mapping):
            if "items" in data:
                replace = data.get("replace", data.get("_replace", False))
                return {"items": data.get("items", []), "replace": replace}
            allowed = {"_replace", "replace"}
            dynamic_items = [key for key in data if key not in allowed]
            if dynamic_items:
                raise ValueError(
                    "List metadata mappings must use `items` and optional `_replace` keys."
                )
            replace = data.get("replace", data.get("_replace", False))
            return {"items": [], "replace": replace}
        return data

    @root_validator(pre=True, allow_reuse=True)
    @classmethod
    def _normalize(cls, data: Any) -> Any:
        return cls.normalize_data(data)


class TemplateMetadata(MetadataModel):
    description: Optional[str] = None
    copy_mode: Optional[CopyMode] = None
    render: Optional[RenderMetadata] = None
    include: Optional[MetadataPatternList] = None
    exclude: Optional[MetadataPatternList] = None
    defaults: Dict[str, ScalarValue] = Field(default_factory=dict)
    variables: Dict[str, VariableDefinition] = Field(default_factory=dict)

    @validator("include", "exclude", pre=True, allow_reuse=True)
    def _normalize_pattern_lists(cls, value: Any) -> Any:
        if value is None:
            return value
        return MetadataPatternList.normalize_data(value)

    @root_validator(pre=True, allow_reuse=True)
    @classmethod
    def _reject_disallowed_fields(cls, data: Any) -> Any:
        if not isinstance(data, Mapping):
            return data

        disallowed = sorted(DISALLOWED_TEMPLATE_METADATA_FIELDS.intersection(data))
        if disallowed:
            field_names = ", ".join(disallowed)
            raise ValueError(f"Disallowed metadata field(s): {field_names}.")

        return data


class EffectiveMetadata(MetadataModel):
    description: Optional[str] = None
    copy_mode: Optional[CopyMode] = None
    render: RenderMetadata = Field(default_factory=RenderMetadata)
    include: List[str] = Field(default_factory=list)
    exclude: List[str] = Field(default_factory=list)
    defaults: Dict[str, ScalarValue] = Field(default_factory=dict)
    variables: Dict[str, VariableDefinition] = Field(default_factory=dict)

    @property
    def render_paths(self) -> bool:
        return self.render.path_names is not False

    @property
    def render_text_files(self) -> bool:
        return self.render.text_files is not False

    @property
    def render_policy(self) -> Dict[str, List[str]]:
        return {"include": list(self.include), "exclude": list(self.exclude)}

    def output_relative_path(self, source_relative_path: Path, rendered_name: str) -> Path:
        if not source_relative_path.parts:
            return Path(rendered_name)

        rendered_parts = list(source_relative_path.parts[:-1])
        rendered_parts.append(rendered_name)
        return Path(*rendered_parts)
