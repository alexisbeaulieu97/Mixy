"""End-to-end project generation pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import List, Optional, Union

from mixy.application.composition import build_generation_executor
from mixy.application.ports import ConfigLoader, MetadataResolverFactory, VarsFileLoader
from mixy.application.services import SourceResolver, TemplateRenderer
from mixy.application.use_cases.plan_project import plan_project
from mixy.application.use_cases.validate_project import ValidationFn
from mixy.domain.exceptions import MergeConflictError
from mixy.domain.models import (
    Conflict,
    CopyRaw,
    CreateDir,
    Overwrite,
    RenderPlan,
    RenderTemplate,
    SkipExisting,
)
from mixy.domain.services import MergePlanner, VariableResolver
from mixy.infrastructure.filesystem.file_writer import GenerationExecutor, GenerationResult


def generate_project(
    config_path: Path,
    *,
    output_override: Optional[Path] = None,
    var_overrides: Optional[Mapping[str, object]] = None,
    vars_file: Optional[Path] = None,
    non_interactive: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
    config_loader: Optional[ConfigLoader] = None,
    vars_file_loader: Optional[VarsFileLoader] = None,
    config_validator: Optional[ValidationFn] = None,
    variable_resolver: Optional[VariableResolver] = None,
    source_resolver: Optional[SourceResolver] = None,
    template_renderer: Optional[TemplateRenderer] = None,
    metadata_resolver_factory: Optional[MetadataResolverFactory] = None,
    merge_planner: Optional[MergePlanner] = None,
    executor: Optional[GenerationExecutor] = None,
) -> Union[GenerationResult, str]:
    generation_executor = build_generation_executor(executor)

    try:
        planned = plan_project(
            config_path,
            output_override=output_override,
            var_overrides=var_overrides,
            vars_file=vars_file,
            non_interactive=non_interactive,
            overwrite=overwrite,
            config_loader=config_loader,
            vars_file_loader=vars_file_loader,
            config_validator=config_validator,
            variable_resolver=variable_resolver,
            source_resolver=source_resolver,
            template_renderer=template_renderer,
            metadata_resolver_factory=metadata_resolver_factory,
            merge_planner=merge_planner,
        )
    except MergeConflictError as error:
        if dry_run:
            return format_conflicts(error.conflicts)
        raise

    if dry_run:
        return format_plan(planned.plan)

    return generation_executor.execute(planned.plan)


def format_plan(result: RenderPlan) -> str:
    lines = ["Action | Output Path | Source"]

    for operation in result.operations:
        if isinstance(operation, CreateDir):
            lines.append(f"create_dir | {operation.path} | -")
        elif isinstance(operation, CopyRaw):
            lines.append(f"copy_raw   | {operation.output_path} | {operation.source_id}")
        elif isinstance(operation, RenderTemplate):
            lines.append(f"render     | {operation.output_path} | {operation.source_id}")
        elif isinstance(operation, Overwrite):
            lines.append(f"overwrite  | {operation.output_path} | {operation.source_id}")
        elif isinstance(operation, SkipExisting):
            lines.append(f"skip       | {operation.output_path} | -")

    if result.conflicts:
        lines.append("Conflicts:")
        for conflict in result.conflicts:
            lines.append(
                f"{conflict.type} | {conflict.path} | "
                f"{conflict.source_a_id} vs {conflict.source_b_id}"
            )

    return "\n".join(lines)


def format_conflicts(conflicts: List[Conflict]) -> str:
    lines = ["Conflicts:"]
    for conflict in conflicts:
        lines.append(
            f"{conflict.type} | {conflict.path} | {conflict.source_a_id} vs {conflict.source_b_id}"
        )
    return "\n".join(lines)
