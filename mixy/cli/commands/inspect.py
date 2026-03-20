"""Config inspection command."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer

from mixy.application.use_cases import inspect_project
from mixy.cli.errors import format_validation_issue, raise_cli_error
from mixy.domain.services import ValidationIssue, VariableResolver


def inspect_config(
    config_path: Path = typer.Argument(..., help="Path to the Mixy config file."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Override the output path used for merge preview.",
    ),
    var: Optional[List[str]] = typer.Option(
        None,
        "--var",
        help="Override a variable with KEY=VALUE. Repeatable.",
        metavar="KEY=VALUE",
    ),
    vars_file: Optional[Path] = typer.Option(
        None,
        "--vars-file",
        help="Load variable overrides from a YAML file.",
    ),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Fail instead of prompting when required variables are unresolved.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Preview overwrite conflict handling regardless of config policy.",
    ),
) -> None:
    """Inspect resolved variables, sources, and merge outputs."""
    try:
        report = inspect_project(
            config_path,
            output_override=output,
            var_overrides=VariableResolver().parse_cli_overrides(var or []),
            vars_file=vars_file,
            non_interactive=non_interactive,
            overwrite=overwrite,
        )
    except Exception as error:
        raise_cli_error(error)

    _echo_validation_warnings(report.validation_issues)

    typer.echo("Config")
    typer.echo("Name | %s" % report.summary.name)
    typer.echo("Version | %s" % report.summary.version)
    typer.echo("Sources | %s" % report.summary.source_count)
    typer.echo("")
    typer.echo("Variables")
    typer.echo("Name | Type | Value | Source")
    for variable in report.variables or []:
        value = "***" if variable.secret and variable.value is not None else (
            "unresolved" if variable.value is None else str(variable.value)
        )
        typer.echo(
            "%s | %s | %s | %s"
            % (variable.name, variable.variable_type, value, variable.value_source.value)
        )
    if not report.variables:
        typer.echo("- | - | - | -")
    typer.echo("")
    typer.echo("Sources")
    typer.echo("Id | Type | Path/URL")
    for source in report.sources:
        typer.echo("%s | %s | %s" % (source.source_id, source.source_type, source.location))
    typer.echo("")
    typer.echo("Merge Preview")
    typer.echo("Source | Output Path | Action")
    for row in report.merge_preview or []:
        typer.echo("%s | %s | %s" % (row.source_id, row.output_path, row.action))
    if not report.merge_preview:
        typer.echo("- | - | -")


def _echo_validation_warnings(issues: list[ValidationIssue]) -> None:
    for issue in issues:
        if issue.severity == "warning":
            typer.echo(format_validation_issue(issue), err=True)
