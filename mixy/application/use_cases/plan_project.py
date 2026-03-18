"""Shared project preparation and planning use cases."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from mixy.application.composition import (
    PlanningDependencies,
    build_config_loader,
    build_metadata_resolver_factory,
    build_planning_dependencies,
    build_vars_file_loader,
)
from mixy.application.ports import ConfigLoader, MetadataResolverFactory, VarsFileLoader
from mixy.application.services import SourceResolver, TemplateRenderer, VariableResolutionService
from mixy.domain.enums import ConflictPolicy
from mixy.domain.exceptions import ConfigValidationError
from mixy.domain.models import (
    EffectiveMetadata,
    MaterializedSource,
    OutputDefinition,
    ProjectDefinition,
    RenderedFile,
    RenderPlan,
    ScalarValue,
    TemplateMetadata,
    TemplateReference,
)
from mixy.domain.models.pre_merge_artifact import PreMergeArtifact, PreMergeEntry
from mixy.domain.services import (
    MergePlanner,
    ValidationIssue,
    VariableResolver as DomainVariableResolver,
    is_metadata_path,
)
ValidationFn = Callable[[ProjectDefinition], list[ValidationIssue]]
RenderDecisionKey = tuple[str, str]
RenderDecisionMap = dict[RenderDecisionKey, RenderedFile]


@dataclass(frozen=True, slots=True)
class PreparedProject:
    definition: ProjectDefinition
    validation_issues: list[ValidationIssue]
    cli_overrides: dict[str, object]
    vars_file_values: dict[str, object]
    env_values: dict[str, str]
    resolved_variables: dict[str, ScalarValue]
    materialized_sources: list[MaterializedSource]
    render_decisions: RenderDecisionMap
    pre_merge_artifact: PreMergeArtifact


@dataclass(frozen=True, slots=True)
class PlannedProject:
    prepared: PreparedProject
    output_definition: OutputDefinition
    plan: RenderPlan


def prepare_project(
    config_path: Path,
    *,
    var_overrides: Mapping[str, object] | None = None,
    vars_file: Path | None = None,
    non_interactive: bool = False,
    config_loader: ConfigLoader | None = None,
    vars_file_loader: VarsFileLoader | None = None,
    config_validator: ValidationFn | None = None,
    variable_resolver: VariableResolutionService | DomainVariableResolver | None = None,
    source_resolver: SourceResolver | None = None,
    template_renderer: TemplateRenderer | None = None,
    metadata_resolver_factory: MetadataResolverFactory | None = None,
    planning_dependencies: PlanningDependencies | None = None,
) -> PreparedProject:
    validator = config_validator or _default_validator
    resolved_config_loader = build_config_loader(config_loader)
    resolved_vars_file_loader = build_vars_file_loader(vars_file_loader)
    resolved_metadata_factory = build_metadata_resolver_factory(metadata_resolver_factory)
    dependencies = planning_dependencies or build_planning_dependencies(
        variable_resolver=variable_resolver,
        source_resolver=source_resolver,
        template_renderer=template_renderer,
    )
    variables = dependencies.variable_resolution_service
    sources_service = dependencies.source_resolver
    renderer = dependencies.template_renderer

    definition = resolved_config_loader(config_path)
    issues = validator(definition)
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        raise ConfigValidationError(
            f"Config validation failed with {len(errors)} error(s).",
            suggestion=f"Run `mixy validate {config_path}` to inspect all validation issues.",
            details=[f"{issue.field_path}: {issue.message}" for issue in errors],
        )

    vars_file_values = resolved_vars_file_loader(vars_file) if vars_file is not None else {}
    cli_overrides = dict(var_overrides or {})
    env_values = variables.read_env_values(definition.variables)
    resolved_global = variables.resolve_all(
        definition.variables,
        global_values=definition.values,
        cli_overrides=cli_overrides,
        vars_file_values=vars_file_values,
        non_interactive=non_interactive,
    )

    materialized_sources = _resolve_sources(sources_service, definition.sources)
    render_decisions, pre_merge_artifact = build_render_artifacts(
        definition=definition,
        materialized_sources=materialized_sources,
        resolved_global=resolved_global,
        cli_overrides=cli_overrides,
        vars_file_values=vars_file_values,
        non_interactive=non_interactive,
        variable_resolver=variables,
        template_renderer=renderer,
        metadata_resolver_factory=resolved_metadata_factory,
    )

    return PreparedProject(
        definition=definition,
        validation_issues=issues,
        cli_overrides=cli_overrides,
        vars_file_values=vars_file_values,
        env_values=env_values,
        resolved_variables=resolved_global,
        materialized_sources=materialized_sources,
        render_decisions=render_decisions,
        pre_merge_artifact=pre_merge_artifact,
    )


def plan_project(
    config_path: Path,
    *,
    output_override: Path | None = None,
    fallback_output_path: Path | None = None,
    var_overrides: Mapping[str, object] | None = None,
    vars_file: Path | None = None,
    non_interactive: bool = False,
    overwrite: bool = False,
    config_loader: ConfigLoader | None = None,
    vars_file_loader: VarsFileLoader | None = None,
    config_validator: ValidationFn | None = None,
    variable_resolver: VariableResolutionService | DomainVariableResolver | None = None,
    source_resolver: SourceResolver | None = None,
    template_renderer: TemplateRenderer | None = None,
    metadata_resolver_factory: MetadataResolverFactory | None = None,
    merge_planner: MergePlanner | None = None,
) -> PlannedProject:
    dependencies = build_planning_dependencies(
        variable_resolver=variable_resolver,
        source_resolver=source_resolver,
        template_renderer=template_renderer,
        merge_planner=merge_planner,
    )
    prepared = prepare_project(
        config_path,
        var_overrides=var_overrides,
        vars_file=vars_file,
        non_interactive=non_interactive,
        config_loader=config_loader,
        vars_file_loader=vars_file_loader,
        config_validator=config_validator,
        variable_resolver=variable_resolver,
        source_resolver=source_resolver,
        template_renderer=template_renderer,
        metadata_resolver_factory=metadata_resolver_factory,
        planning_dependencies=dependencies,
    )
    planner = dependencies.merge_planner
    output_definition = resolve_output_definition(
        prepared.definition,
        output_override,
        overwrite=overwrite,
        fallback_output_path=fallback_output_path,
    )
    pre_merge_artifact = getattr(prepared, "pre_merge_artifact", None)
    if pre_merge_artifact is None:
        plan = planner.build_plan(
            prepared.materialized_sources,
            output_definition,
            prepared.render_decisions,
        )
    else:
        plan = planner.build_plan(
            prepared.materialized_sources,
            output_definition,
            prepared.render_decisions,
            pre_merge_artifact=pre_merge_artifact,
        )
    return PlannedProject(
        prepared=prepared,
        output_definition=output_definition,
        plan=plan,
    )


def resolve_output_definition(
    definition: ProjectDefinition,
    output_override: Path | None,
    *,
    overwrite: bool,
    fallback_output_path: Path | None = None,
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
        if fallback_output_path is None:
            raise ValueError("Config must define an output path or provide an output override.")
        fallback_policy = ConflictPolicy.OVERWRITE if overwrite else ConflictPolicy.FAIL
        return OutputDefinition(path=fallback_output_path, conflict_policy=fallback_policy)

    if overwrite:
        return definition.output.model_copy(update={"conflict_policy": ConflictPolicy.OVERWRITE})

    return definition.output


def _resolve_sources(
    sources_service: SourceResolver,
    references: list[TemplateReference],
) -> list[MaterializedSource]:
    """Resolve sources while keeping the public planning API synchronous."""
    enabled_references = [reference for reference in references if reference.enabled]
    if len(enabled_references) <= 1:
        return sources_service.resolve_all(references)

    return _resolve_sources_concurrently(sources_service, enabled_references)


def _resolve_sources_concurrently(
    sources_service: SourceResolver,
    references: list[TemplateReference],
) -> list[MaterializedSource]:
    results: list[MaterializedSource | None] = [None] * len(references)
    max_workers = min(len(references), 32)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures: list[Future[list[MaterializedSource]]] = [
            executor.submit(sources_service.resolve_all, [reference])
            for reference in references
        ]

        for index, future in enumerate(futures):
            result = future.result()
            results[index] = result[0] if result else None

    return [result for result in results if result is not None]


def build_render_artifacts(
    *,
    definition: ProjectDefinition,
    materialized_sources: list[MaterializedSource],
    resolved_global: Mapping[str, ScalarValue],
    cli_overrides: Mapping[str, object],
    vars_file_values: Mapping[str, object],
    non_interactive: bool,
    variable_resolver: VariableResolutionService,
    template_renderer: TemplateRenderer,
    metadata_resolver_factory: MetadataResolverFactory,
) -> tuple[RenderDecisionMap, PreMergeArtifact]:
    decisions: RenderDecisionMap = {}
    directory_paths: dict[Path, list[str]] = {Path("."): ["<output>"]}
    file_entries: list[PreMergeEntry] = []
    project_defaults = TemplateMetadata(
        variables=definition.variables,
        defaults=dict(definition.values),
    )

    by_id = {source.source_id: source for source in materialized_sources}
    for reference in definition.sources:
        if not reference.enabled:
            continue
        (
            source_decisions,
            source_directory_paths,
            source_file_entries,
        ) = _build_source_render_artifacts(
            definition=definition,
            reference=reference,
            materialized=by_id[reference.id],
            project_defaults=project_defaults,
            resolved_global=resolved_global,
            cli_overrides=cli_overrides,
            vars_file_values=vars_file_values,
            non_interactive=non_interactive,
            variable_resolver=variable_resolver,
            template_renderer=template_renderer,
            metadata_resolver_factory=metadata_resolver_factory,
        )
        decisions.update(source_decisions)
        file_entries.extend(source_file_entries)
        for directory_path, owner_ids in source_directory_paths.items():
            directory_paths.setdefault(directory_path, []).extend(owner_ids)

    return decisions, PreMergeArtifact(
        directory_paths=directory_paths,
        file_entries=file_entries,
    )


def _build_source_render_artifacts(
    *,
    definition: ProjectDefinition,
    reference: TemplateReference,
    materialized: MaterializedSource,
    project_defaults: TemplateMetadata,
    resolved_global: Mapping[str, ScalarValue],
    cli_overrides: Mapping[str, object],
    vars_file_values: Mapping[str, object],
    non_interactive: bool,
    variable_resolver: VariableResolutionService,
    template_renderer: TemplateRenderer,
    metadata_resolver_factory: MetadataResolverFactory,
) -> tuple[RenderDecisionMap, dict[Path, list[str]], list[PreMergeEntry]]:
    metadata_resolver = metadata_resolver_factory(materialized.root_path)
    decisions: RenderDecisionMap = {}
    directory_paths: dict[Path, list[str]] = {}
    file_entries: list[PreMergeEntry] = []

    for source_path in _iter_source_paths(materialized.root_path):
        relative = source_path.relative_to(materialized.root_path)
        if is_metadata_path(relative):
            continue
        if source_path.is_dir():
            directory_paths.setdefault(relative, []).append(materialized.source_id)
            continue

        decision_key, rendered_file = _build_file_render_decision(
            definition=definition,
            reference=reference,
            source_path=source_path,
            relative=relative,
            materialized=materialized,
            metadata_resolver=metadata_resolver,
            project_defaults=project_defaults,
            resolved_global=resolved_global,
            cli_overrides=cli_overrides,
            vars_file_values=vars_file_values,
            non_interactive=non_interactive,
            variable_resolver=variable_resolver,
            template_renderer=template_renderer,
        )
        decisions[decision_key] = rendered_file
        file_entries.append(
            PreMergeEntry(
                source_id=reference.id,
                source_path=source_path,
                relative_path=relative,
                output_relative_path=rendered_file.output_relative_path
                or relative.parent / rendered_file.output_name,
                rendered_file=rendered_file,
            )
        )

    return decisions, directory_paths, file_entries


def _build_file_render_decision(
    *,
    definition: ProjectDefinition,
    reference: TemplateReference,
    source_path: Path,
    relative: Path,
    materialized: MaterializedSource,
    metadata_resolver: MetadataResolver,
    project_defaults: TemplateMetadata,
    resolved_global: Mapping[str, ScalarValue],
    cli_overrides: Mapping[str, object],
    vars_file_values: Mapping[str, object],
    non_interactive: bool,
    variable_resolver: VariableResolutionService,
    template_renderer: TemplateRenderer,
) -> tuple[RenderDecisionKey, RenderedFile]:
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
    return (
        (reference.id, relative.as_posix()),
        RenderedFile(
            output_name=output_relative.name,
            content=rendered.content,
            rendered=rendered.rendered,
            is_binary=rendered.is_binary,
            output_relative_path=output_relative,
        ),
    )
def _iter_source_paths(root_path: Path) -> list[Path]:
    return sorted(root_path.rglob("*"))


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
def _default_validator(definition: ProjectDefinition) -> list[ValidationIssue]:
    from mixy.domain.services.config_validator import validate

    return validate(definition)
