"""Config inspection command."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Annotated

import typer

from mixy.application.use_cases.generate_project import build_render_decisions
from mixy.cli.errors import USER_ERROR_EXIT_CODE, format_validation_issue, raise_cli_error
from mixy.domain.enums import ConflictPolicy
from mixy.domain.models import (
    FileOperation,
    OutputDefinition,
    ProjectDefinition,
    ScalarValue,
    VariableDefinition,
)
from mixy.domain.services import (
    MergePlanner,
    SourceResolver,
    TemplateRenderer,
    ValidationIssue,
    VariableResolver,
    validate,
)
from mixy.infrastructure.config import load_config, load_vars_file
from mixy.infrastructure.sources.git import GitSourceProvider
from mixy.infrastructure.sources.local import LocalDirProvider


def inspect_config(
    config_path: Annotated[
        Path,
        typer.Argument(help="Path to the Mixy config file."),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Override the output path used for merge preview."),
    ] = None,
    var: Annotated[
        list[str] | None,
        typer.Option(
            "--var",
            help="Override a variable with KEY=VALUE. Repeatable.",
            metavar="KEY=VALUE",
        ),
    ] = None,
    vars_file: Annotated[
        Path | None,
        typer.Option("--vars-file", help="Load variable overrides from a YAML file."),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            help="Fail instead of prompting when required variables are unresolved.",
        ),
    ] = False,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Preview overwrite conflict handling regardless of config policy.",
        ),
    ] = False,
) -> None:
    """Inspect resolved variables, sources, and merge outputs."""
    variable_resolver = VariableResolver()
    source_resolver = SourceResolver([LocalDirProvider(), GitSourceProvider()])
    merge_planner = MergePlanner()
    template_renderer = TemplateRenderer()

    try:
        definition = load_config(config_path)
        _exit_on_validation_errors(validate(definition))
        cli_overrides = variable_resolver.parse_cli_overrides(var or [])
        vars_file_values = load_vars_file(vars_file) if vars_file is not None else {}
        resolved_variables = variable_resolver.resolve_all(
            definition.variables,
            global_values=definition.values,
            cli_overrides=cli_overrides,
            vars_file_values=vars_file_values,
            non_interactive=non_interactive,
        )
        sources = source_resolver.resolve_all(definition.sources)
        render_decisions = build_render_decisions(
            definition=definition,
            materialized_sources=sources,
            resolved_global=resolved_variables,
            cli_overrides=cli_overrides,
            vars_file_values=vars_file_values,
            non_interactive=non_interactive,
            variable_resolver=variable_resolver,
            template_renderer=template_renderer,
        )
        plan = merge_planner.build_plan(
            sources,
            _resolve_output_definition(definition, output=output, overwrite=overwrite),
            render_decisions,
        )
    except Exception as error:
        raise_cli_error(error)

    typer.echo("Config")
    typer.echo(f"Name | {definition.name or '-'}")
    typer.echo(f"Version | {definition.version}")
    typer.echo(f"Sources | {len(definition.sources)}")
    typer.echo("")
    typer.echo("Variables")
    typer.echo("Name | Type | Value | Source")
    for line in _format_variable_rows(
        definition.variables,
        resolved_variables,
        global_values=definition.values,
        vars_file_values=vars_file_values,
        cli_overrides=cli_overrides,
        env_values=variable_resolver.read_env_values(definition.variables),
    ):
        typer.echo(line)
    typer.echo("")
    typer.echo("Sources")
    typer.echo("Id | Type | Path/URL")
    for reference in definition.sources:
        location = _source_location(reference.source)
        typer.echo(f"{reference.id} | {reference.source.type} | {location}")
    typer.echo("")
    typer.echo("Merge Preview")
    typer.echo("Source | Output Path | Action")
    for line in _format_preview_rows(plan.operations):
        typer.echo(line)


def _exit_on_validation_errors(issues: Sequence[ValidationIssue]) -> None:
    error_issues = [issue for issue in issues if issue.severity == "error"]
    warning_issues = [issue for issue in issues if issue.severity == "warning"]

    for issue in warning_issues:
        typer.echo(format_validation_issue(issue), err=True)

    if error_issues:
        for issue in error_issues:
            typer.echo(format_validation_issue(issue), err=True)
        raise typer.Exit(code=USER_ERROR_EXIT_CODE)


def _format_variable_rows(
    definitions: Mapping[str, VariableDefinition],
    resolved_variables: Mapping[str, ScalarValue],
    *,
    global_values: Mapping[str, object],
    vars_file_values: Mapping[str, object],
    cli_overrides: Mapping[str, object],
    env_values: Mapping[str, str],
) -> list[str]:
    rows: list[str] = []

    for name, definition in definitions.items():
        value = resolved_variables.get(name)
        source = _variable_source(
            name,
            definition,
            resolved_variables=resolved_variables,
            global_values=global_values,
            vars_file_values=vars_file_values,
            cli_overrides=cli_overrides,
            env_values=env_values,
        )
        rows.append(
            f"{name} | {definition.type.value} | {_display_value(definition, value)} | {source}"
        )

    if rows:
        return rows
    return ["- | - | - | -"]


def _variable_source(
    name: str,
    definition: VariableDefinition,
    *,
    resolved_variables: Mapping[str, ScalarValue],
    global_values: Mapping[str, object],
    vars_file_values: Mapping[str, object],
    cli_overrides: Mapping[str, object],
    env_values: Mapping[str, str],
) -> str:
    if name in cli_overrides:
        return "cli"
    if name in vars_file_values:
        return "vars-file"
    if name in env_values:
        return "env"
    if name in global_values:
        return "config"
    if definition.default is not None:
        return "default"
    if name in resolved_variables:
        return "prompt"
    return "unresolved"


def _display_value(definition: VariableDefinition, value: ScalarValue | None) -> str:
    if value is None:
        return "unresolved"
    if definition.secret:
        return "***"
    return str(value)


def _source_location(source: object) -> str:
    if hasattr(source, "path"):
        return str(source.path)
    if hasattr(source, "url"):
        return str(source.url)
    return "-"


def _format_preview_rows(operations: Sequence[FileOperation]) -> list[str]:
    by_source: dict[str, list[str]] = defaultdict(list)

    for operation in operations:
        if not hasattr(operation, "source_id") or not hasattr(operation, "output_path"):
            continue
        action = operation.__class__.__name__.lower()
        by_source[operation.source_id].append(
            f"{operation.source_id} | {operation.output_path} | {action}"
        )

    rows = [line for source_id in sorted(by_source) for line in by_source[source_id]]
    if rows:
        return rows
    return ["- | - | -"]


def _resolve_output_definition(
    definition: ProjectDefinition,
    *,
    output: Path | None,
    overwrite: bool,
) -> OutputDefinition:
    if output is not None:
        conflict_policy = (
            definition.output.conflict_policy
            if definition.output is not None
            else ConflictPolicy.FAIL
        )
        if overwrite:
            conflict_policy = ConflictPolicy.OVERWRITE
        return OutputDefinition(path=output, conflict_policy=conflict_policy)

    if definition.output is None:
        fallback_policy = ConflictPolicy.OVERWRITE if overwrite else ConflictPolicy.FAIL
        return OutputDefinition(path=Path("<output>"), conflict_policy=fallback_policy)

    if overwrite:
        return definition.output.model_copy(update={"conflict_policy": ConflictPolicy.OVERWRITE})

    return definition.output
