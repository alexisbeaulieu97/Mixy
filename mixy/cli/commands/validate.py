"""Config validation command."""

from __future__ import annotations

from pathlib import Path

import typer

from mixy.application.use_cases import validate_project
from mixy.cli.errors import USER_ERROR_EXIT_CODE, format_validation_issue, raise_cli_error


def validate_config(
    config_path: Path = typer.Argument(..., help="Path to the Mixy config file."),
) -> None:
    """Validate a Mixy config without generating files."""
    try:
        issues = validate_project(config_path)
    except Exception as error:
        raise_cli_error(error)

    error_issues = [issue for issue in issues if issue.severity == "error"]
    warning_issues = [issue for issue in issues if issue.severity == "warning"]

    for issue in warning_issues:
        typer.echo(format_validation_issue(issue), err=True)

    if error_issues:
        for issue in error_issues:
            typer.echo(format_validation_issue(issue), err=True)
        raise typer.Exit(code=USER_ERROR_EXIT_CODE)

    typer.echo("Config is valid: %s" % config_path)
