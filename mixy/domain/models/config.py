"""Pydantic models for Mixy's project configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

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


class LocalFileSource(MixyModel):
    type: Literal["local_file"]
    path: Path


class GitSource(MixyModel):
    type: Literal["git"]
    url: str
    ref: str
    subpath: str | None = None


SourceDefinition: TypeAlias = Annotated[
    LocalDirSource | LocalFileSource | GitSource,
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
