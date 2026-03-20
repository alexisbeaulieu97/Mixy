"""Pydantic models for Mixy's project configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union

from pydantic import BaseModel, Field, StrictBool, StrictFloat, StrictInt, StrictStr, validator
from typing_extensions import Annotated, Literal

from mixy.domain.enums import ConflictPolicy, VariableType

ScalarValue = Union[StrictStr, StrictInt, StrictFloat, StrictBool]
MixyModelT = TypeVar("MixyModelT", bound="MixyModel")


class MixyModel(BaseModel):
    """Base model with strict schema handling."""

    class Config:
        extra = "forbid"

    @classmethod
    def model_validate(cls: Type[MixyModelT], data: Any) -> MixyModelT:
        return cls.parse_obj(data)

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return self.dict(**kwargs)

    def model_copy(self: MixyModelT, **kwargs: Any) -> MixyModelT:
        return self.copy(**kwargs)

    @classmethod
    def model_construct(cls: Type[MixyModelT], **values: Any) -> MixyModelT:
        return cls.construct(**values)

    @property
    def model_fields_set(self) -> Set[str]:
        return set(self.__fields_set__)


class VariableDefinition(MixyModel):
    type: VariableType
    required: bool = True
    default: Optional[ScalarValue] = None
    description: Optional[str] = None
    choices: Optional[List[ScalarValue]] = None
    examples: Optional[List[ScalarValue]] = None
    pattern: Optional[str] = None
    secret: bool = False

    @validator("default", allow_reuse=True)
    def _validate_default(
        cls,
        value: Optional[ScalarValue],
        values: Dict[str, Any],
    ) -> Optional[ScalarValue]:
        variable_type = values.get("type")
        if value is not None and variable_type is not None and not _matches_variable_type(
            variable_type, value
        ):
            raise ValueError("Default value does not match the declared variable type.")
        return value

    @validator("choices", allow_reuse=True)
    def _validate_choices(
        cls,
        value: Optional[List[ScalarValue]],
        values: Dict[str, Any],
    ) -> Optional[List[ScalarValue]]:
        variable_type = values.get("type")
        if value is None or variable_type is None:
            return value
        for choice in value:
            if not _matches_variable_type(variable_type, choice):
                raise ValueError("Choice value does not match the declared variable type.")
        return value


class LocalDirSource(MixyModel):
    type: Literal["local_dir"]
    path: Path
    subpath: Optional[str] = None


class GitSource(MixyModel):
    type: Literal["git"]
    url: str
    ref: str
    subpath: Optional[str] = None


SourceDefinition = Annotated[
    Union[LocalDirSource, GitSource],
    Field(discriminator="type"),
]


class TemplateReference(MixyModel):
    id: str
    source: SourceDefinition
    subpath: Optional[str] = None
    alias: Optional[str] = None
    enabled: bool = True
    values: Dict[str, ScalarValue] = Field(default_factory=dict)
    merge_strategy: Optional[str] = None

    @validator("merge_strategy", allow_reuse=True)
    @classmethod
    def _reject_merge_strategy(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            raise ValueError("merge_strategy is unsupported for source entries.")
        return value

    @validator("subpath", allow_reuse=True)
    def _validate_subpath(cls, value: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        source = values.get("source")
        if value is not None and getattr(source, "type", None) == "git":
            raise ValueError(
                "Reference-level subpath is not supported for git sources; use source.subpath."
            )
        return value


class OutputDefinition(MixyModel):
    path: Path
    conflict_policy: ConflictPolicy = ConflictPolicy.FAIL


class ProjectDefinition(MixyModel):
    version: str
    name: Optional[str] = None
    description: Optional[str] = None
    sources: List[TemplateReference]
    variables: Dict[str, VariableDefinition] = Field(default_factory=dict)
    values: Dict[str, ScalarValue] = Field(default_factory=dict)
    output: Optional[OutputDefinition] = None


def _matches_variable_type(expected: VariableType, value: object) -> bool:
    if expected is VariableType.STR:
        return isinstance(value, str)
    if expected is VariableType.INT:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected is VariableType.FLOAT:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, bool)
