"""End-to-end project generation pipeline."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from mixy.domain.enums import ConflictPolicy
from mixy.domain.exceptions import ConfigValidationError, MergeConflictError
from mixy.domain.models import (
    Conflict,
    EffectiveMetadata,
    MaterializedSource,
    OutputDefinition,
    ProjectDefinition,
    RenderedFile,
    RenderPlan,
    ScalarValue,
    TemplateMetadata,
)
from mixy.domain.services import (
    MergePlanner,
    MetadataResolver,
    SourceResolver,
    TemplateRenderer,
    ValidationIssue,
    VariableResolver,
    is_metadata_path,
)
from mixy.infrastructure.config import MetadataLoader, load_config, load_vars_file
from mixy.infrastructure.filesystem.file_writer import GenerationExecutor, GenerationResult
from mixy.infrastructure.sources.git import GitSourceProvider
from mixy.infrastructure.sources.local import LocalDirProvider

ConfigLoader = Callable[[Path], ProjectDefinition]
VarsFileLoader = Callable[[Path], dict[str, object]]
ValidationFn = Callable[[ProjectDefinition], list[ValidationIssue]]


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
    validator = config_validator or _default_validator
    variables = variable_resolver or VariableResolver()
    sources_service = source_resolver or SourceResolver([LocalDirProvider(), GitSourceProvider()])
    renderer = template_renderer or TemplateRenderer()
    planner = merge_planner or MergePlanner()
    generation_executor = executor or GenerationExecutor()

    definition = config_loader(config_path)
    issues = validator(definition)
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        raise ConfigValidationError(
            f"Config validation failed with {len(errors)} error(s).",
            suggestion=f"Run `mixy validate {config_path}` to inspect all validation issues.",
            details=[f"{issue.field_path}: {issue.message}" for issue in errors],
        )

    vars_file_values = vars_file_loader(vars_file) if vars_file is not None else {}
    cli_overrides = dict(var_overrides or {})
    resolved_global = variables.resolve_all(
        definition.variables,
        global_values=definition.values,
        cli_overrides=cli_overrides,
        vars_file_values=vars_file_values,
        non_interactive=non_interactive,
    )

    materialized_sources = sources_service.resolve_all(definition.sources)
    render_decisions = build_render_decisions(
        definition=definition,
        materialized_sources=materialized_sources,
        resolved_global=resolved_global,
        cli_overrides=cli_overrides,
        vars_file_values=vars_file_values,
        non_interactive=non_interactive,
        variable_resolver=variables,
        template_renderer=renderer,
    )

    output_definition = _resolve_output_definition(definition, output_override, overwrite=overwrite)

    try:
        plan = planner.build_plan(materialized_sources, output_definition, render_decisions)
    except MergeConflictError as error:
        if dry_run:
            return format_conflicts(error.conflicts)
        raise

    if dry_run:
        return format_plan(plan)

    return generation_executor.execute(plan)


def build_render_decisions(
    *,
    definition: ProjectDefinition,
    materialized_sources: list[MaterializedSource],
    resolved_global: Mapping[str, ScalarValue],
    cli_overrides: Mapping[str, object],
    vars_file_values: Mapping[str, object],
    non_interactive: bool,
    variable_resolver: VariableResolver,
    template_renderer: TemplateRenderer,
) -> dict[tuple[str, str], RenderedFile]:
    decisions: dict[tuple[str, str], RenderedFile] = {}
    metadata_loader = MetadataLoader()
    by_id = {source.source_id: source for source in materialized_sources}
    project_defaults = TemplateMetadata(
        variables=definition.variables,
        defaults=dict(definition.values),
    )
    prompt_cache: dict[str, ScalarValue] = {}

    for reference in definition.sources:
        materialized = by_id[reference.id]
        discovered = metadata_loader.discover(materialized.root_path)
        metadata_resolver = MetadataResolver(
            directory_scopes=discovered.directory_scopes,
            file_scopes=discovered.file_scopes,
        )

        for source_path in sorted(
            path for path in materialized.root_path.rglob("*") if path.is_file()
        ):
            relative = source_path.relative_to(materialized.root_path)
            if is_metadata_path(relative):
                continue

            effective = metadata_resolver.resolve_for_file(
                relative,
                materialized.root_path,
                project_defaults,
            )
            source_context = variable_resolver.build_effective_context(
                effective.variables,
                resolved_global,
                global_values=definition.values,
                vars_file_values=vars_file_values,
                source_values=reference.values,
                cli_overrides=cli_overrides,
                default_values=effective.defaults,
                non_interactive=non_interactive,
                prompt_cache=prompt_cache,
            )
            rendered = template_renderer.render_file(
                source_path,
                source_context,
                effective.render_policy,
                copy_mode=effective.copy_mode,
                render_text_files=effective.render_text_files,
            )
            output_relative = _render_output_relative_path(
                relative,
                rendered.output_name,
                source_context,
                effective,
                template_renderer,
            )
            decisions[(reference.id, relative.as_posix())] = RenderedFile(
                output_name=output_relative.name,
                content=rendered.content,
                rendered=rendered.rendered,
                is_binary=rendered.is_binary,
                output_relative_path=output_relative,
            )

    return decisions


def _render_output_relative_path(
    relative_path: Path,
    rendered_name: str,
    context: Mapping[str, ScalarValue],
    metadata: EffectiveMetadata,
    template_renderer: TemplateRenderer,
) -> Path:
    final_name = template_renderer.render_path_segment(
        rendered_name,
        context,
        enabled=metadata.render_paths,
    )
    rendered_parts = [
        template_renderer.render_path_segment(part, context, enabled=metadata.render_paths)
        for part in relative_path.parts[:-1]
    ]
    return Path(*rendered_parts, final_name)


def format_plan(result: RenderPlan) -> str:
    lines = ["Action | Output Path | Source"]

    for operation in result.operations:
        if hasattr(operation, "path"):
            lines.append(f"create_dir | {operation.path} | -")
        else:
            source = getattr(operation, "source_id", "-")
            lines.append(f"{operation.__class__.__name__} | {operation.output_path} | {source}")

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


def _default_validator(definition: ProjectDefinition) -> list[ValidationIssue]:
    from mixy.domain.services.config_validator import validate

    return validate(definition)


def _resolve_output_definition(
    definition: ProjectDefinition,
    output_override: Path | None,
    *,
    overwrite: bool,
) -> OutputDefinition:
    if output_override is not None:
        conflict_policy = (
            definition.output.conflict_policy
            if definition.output is not None
            else ConflictPolicy.FAIL
        )
        if overwrite:
            conflict_policy = ConflictPolicy.OVERWRITE
        return OutputDefinition(path=output_override, conflict_policy=conflict_policy)

    if definition.output is None:
        raise ValueError("Config must define an output path or provide an output override.")

    if overwrite:
        return definition.output.model_copy(update={"conflict_policy": ConflictPolicy.OVERWRITE})

    return definition.output
