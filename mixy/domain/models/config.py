"""Pydantic models for Mixy's project configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from mixy.domain.enums import ConflictPolicy, VariableType

ScalarValue: TypeAlias = str | int | float | bool


class MixyModel(BaseModel):
    """Base model with strict schema handling."""

    model_config = ConfigDict(extra="forbid")


class VariableDefinition(MixyModel):
    type: VariableType
    required: bool = True
    default: ScalarValue | None = None
    description: str | None = None
    choices: list[ScalarValue] | None = None
    examples: list[ScalarValue] | None = None
    pattern: str | None = None
    secret: bool = False


class LocalDirSource(MixyModel):
    type: Literal["local_dir"]
    path: Path
    subpath: str | None = None


class GitSource(MixyModel):
    type: Literal["git"]
    url: str
    ref: str
    subpath: str | None = None


SourceDefinition: TypeAlias = Annotated[
    LocalDirSource | GitSource,
    Field(discriminator="type"),
]


class TemplateReference(MixyModel):
    id: str
    source: SourceDefinition
    subpath: str | None = None
    alias: str | None = None
    enabled: bool = True
    values: dict[str, ScalarValue] = Field(default_factory=dict)
    merge_strategy: str | None = None

    @field_validator("merge_strategy")
    @classmethod
    def _reject_merge_strategy(cls, value: str | None) -> str | None:
        if value is not None:
            raise ValueError("merge_strategy is unsupported for source entries.")
        return value

    @field_validator("subpath")
    @classmethod
    def _validate_subpath(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return value

        source = info.data.get("source")
        if getattr(source, "type", None) == "git":
            raise ValueError(
                "Reference-level subpath is not supported for git sources; use source.subpath."
            )

        return value


class OutputDefinition(MixyModel):
    path: Path
    conflict_policy: ConflictPolicy = ConflictPolicy.FAIL


class ProjectDefinition(MixyModel):
    version: str
    name: str | None = None
    description: str | None = None
    sources: list[TemplateReference]
    variables: dict[str, VariableDefinition] = Field(default_factory=dict)
    values: dict[str, ScalarValue] = Field(default_factory=dict)
    output: OutputDefinition | None = None
