"""Config inspection command."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Annotated

import typer

from mixy.application.use_cases.plan_project import plan_project
from mixy.cli.errors import format_validation_issue, raise_cli_error
from mixy.domain.models import FileOperation, ScalarValue, VariableDefinition
from mixy.domain.services import ValidationIssue, VariableResolver


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
    try:
        planned = plan_project(
            config_path,
            output_override=output,
            fallback_output_path=Path("<output>"),
            var_overrides=VariableResolver().parse_cli_overrides(var or []),
            vars_file=vars_file,
            non_interactive=non_interactive,
            overwrite=overwrite,
        )
    except Exception as error:
        raise_cli_error(error)

    prepared = planned.prepared
    _echo_validation_warnings(prepared.validation_issues)

    typer.echo("Config")
    typer.echo(f"Name | {prepared.definition.name or '-'}")
    typer.echo(f"Version | {prepared.definition.version}")
    typer.echo(f"Sources | {len(prepared.definition.sources)}")
    typer.echo("")
    typer.echo("Variables")
    typer.echo("Name | Type | Value | Source")
    for line in _format_variable_rows(
        prepared.definition.variables,
        prepared.resolved_variables,
        global_values=prepared.definition.values,
        vars_file_values=prepared.vars_file_values,
        cli_overrides=prepared.cli_overrides,
        env_values=prepared.env_values,
    ):
        typer.echo(line)
    typer.echo("")
    typer.echo("Sources")
    typer.echo("Id | Type | Path/URL")
    for reference in prepared.definition.sources:
        location = _source_location(reference.source)
        typer.echo(f"{reference.id} | {reference.source.type} | {location}")
    typer.echo("")
    typer.echo("Merge Preview")
    typer.echo("Source | Output Path | Action")
    for line in _format_preview_rows(planned.plan.operations):
        typer.echo(line)


def _echo_validation_warnings(issues: list[ValidationIssue]) -> None:
    for issue in issues:
        if issue.severity == "warning":
            typer.echo(format_validation_issue(issue), err=True)


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
