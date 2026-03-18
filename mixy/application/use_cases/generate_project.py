"""End-to-end project generation pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from mixy.application.services import SourceResolver, TemplateRenderer
from mixy.application.use_cases.plan_project import (
    ConfigLoader,
    ValidationFn,
    VarsFileLoader,
    plan_project,
)
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
from mixy.infrastructure.config import load_config, load_vars_file
from mixy.infrastructure.filesystem.file_writer import GenerationExecutor, GenerationResult


def generate_project(
    config_path: Path,
    *,
    output_override: Path | None = None,
    var_overrides: Mapping[str, object] | None = None,
    vars_file: Path | None = None,
    non_interactive: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
    config_loader: ConfigLoader = load_config,
    vars_file_loader: VarsFileLoader = load_vars_file,
    config_validator: ValidationFn | None = None,
    variable_resolver: VariableResolver | None = None,
    source_resolver: SourceResolver | None = None,
    template_renderer: TemplateRenderer | None = None,
    merge_planner: MergePlanner | None = None,
    executor: GenerationExecutor | None = None,
) -> GenerationResult | str:
    generation_executor = executor or GenerationExecutor()

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
        match operation:
            case CreateDir(path=p):
                lines.append(f"create_dir | {p} | -")
            case CopyRaw(output_path=p, source_id=s):
                lines.append(f"copy_raw   | {p} | {s}")
            case RenderTemplate(output_path=p, source_id=s):
                lines.append(f"render     | {p} | {s}")
            case Overwrite(output_path=p, source_id=s):
                lines.append(f"overwrite  | {p} | {s}")
            case SkipExisting(output_path=p):
                lines.append(f"skip       | {p} | -")

    if result.conflicts:
        lines.append("Conflicts:")
        for conflict in result.conflicts:
            lines.append(
                f"{conflict.type} | {conflict.path} | "
                f"{conflict.source_a_id} vs {conflict.source_b_id}"
            )

    return "\n".join(lines)


def format_conflicts(conflicts: list[Conflict]) -> str:
    lines = ["Conflicts:"]
    for conflict in conflicts:
        lines.append(
            f"{conflict.type} | {conflict.path} | {conflict.source_a_id} vs {conflict.source_b_id}"
        )
    return "\n".join(lines)
