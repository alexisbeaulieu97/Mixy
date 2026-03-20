"""Application use case for inspection-oriented project reporting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

from mixy.application.use_cases.plan_project import PlannedProject, plan_project
from mixy.domain.enums import ValueSource
from mixy.domain.models import (
    FileOperation,
    GitSource,
    LocalDirSource,
    ScalarValue,
    VariableDefinition,
)
from mixy.domain.services import ValidationIssue


@dataclass(frozen=True)
class InspectionSummary:
    name: str
    version: str
    source_count: int


@dataclass(frozen=True)
class VariableInspection:
    name: str
    variable_type: str
    value: Optional[ScalarValue]
    value_source: ValueSource
    secret: bool


@dataclass(frozen=True)
class SourceInspection:
    source_id: str
    source_type: str
    location: str


@dataclass(frozen=True)
class MergePreviewEntry:
    source_id: str
    output_path: Path
    action: str


@dataclass(frozen=True)
class InspectionReport:
    summary: InspectionSummary
    validation_issues: list[ValidationIssue]
    variables: list[VariableInspection]
    sources: list[SourceInspection]
    merge_preview: list[MergePreviewEntry]


def inspect_project(
    config_path: Path,
    *,
    output_override: Optional[Path] = None,
    var_overrides: Optional[Mapping[str, object]] = None,
    vars_file: Optional[Path] = None,
    non_interactive: bool = False,
    overwrite: bool = False,
) -> InspectionReport:
    planned = plan_project(
        config_path,
        output_override=output_override,
        fallback_output_path=Path("<output>"),
        var_overrides=var_overrides,
        vars_file=vars_file,
        non_interactive=non_interactive,
        overwrite=overwrite,
    )
    return _build_report(planned)


def _build_report(planned: PlannedProject) -> InspectionReport:
    prepared = planned.prepared
    definition = prepared.definition
    return InspectionReport(
        summary=InspectionSummary(
            name=definition.name or "-",
            version=definition.version,
            source_count=len(definition.sources),
        ),
        validation_issues=prepared.validation_issues,
        variables=[
            VariableInspection(
                name=name,
                variable_type=variable.type.value,
                value=prepared.resolved_variables.get(name),
                value_source=_value_source(
                    name,
                    variable,
                    resolved_variables=prepared.resolved_variables,
                    global_values=definition.values,
                    vars_file_values=prepared.vars_file_values,
                    cli_overrides=prepared.cli_overrides,
                    env_values=prepared.env_values,
                ),
                secret=variable.secret,
            )
            for name, variable in definition.variables.items()
        ],
        sources=[
            SourceInspection(
                source_id=reference.id,
                source_type=reference.source.type,
                location=_source_location(reference.source),
            )
            for reference in definition.sources
        ],
        merge_preview=_merge_preview(planned.plan.operations),
    )


def _value_source(
    name: str,
    definition: VariableDefinition,
    *,
    resolved_variables: Mapping[str, ScalarValue],
    global_values: Mapping[str, object],
    vars_file_values: Mapping[str, object],
    cli_overrides: Mapping[str, object],
    env_values: Mapping[str, str],
) -> ValueSource:
    if name in cli_overrides:
        return ValueSource.CLI
    if name in vars_file_values:
        return ValueSource.VARS_FILE
    if name in env_values:
        return ValueSource.ENV
    if name in global_values:
        return ValueSource.CONFIG
    if definition.default is not None:
        return ValueSource.DEFAULT
    if name in resolved_variables:
        return ValueSource.PROMPT
    return ValueSource.UNRESOLVED


def _source_location(source: object) -> str:
    if isinstance(source, LocalDirSource):
        return str(source.path)
    if isinstance(source, GitSource):
        return str(source.url)
    return "-"


def _merge_preview(operations: list[FileOperation]) -> list[MergePreviewEntry]:
    preview: list[MergePreviewEntry] = []
    for operation in operations:
        if not hasattr(operation, "source_id") or not hasattr(operation, "output_path"):
            continue
        preview.append(
            MergePreviewEntry(
                source_id=operation.source_id,
                output_path=operation.output_path,
                action=operation.__class__.__name__.lower(),
            )
        )
    return preview
