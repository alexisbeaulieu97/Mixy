"""Project generation command."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer

from mixy.application.use_cases.generate_project import generate_project
from mixy.cli.errors import raise_cli_error
from mixy.domain.services import VariableResolver


def generate(
    config_path: Path = typer.Argument(..., help="Path to the Mixy config file."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        help="Override the configured output directory.",
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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show the plan without writing files.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite file conflicts regardless of the config conflict policy.",
    ),
) -> None:
    """Generate a project from a Mixy config."""
    variable_resolver = VariableResolver()

    try:
        cli_overrides = variable_resolver.parse_cli_overrides(var or [])
        result = generate_project(
            config_path,
            output_override=output,
            var_overrides=cli_overrides,
            vars_file=vars_file,
            non_interactive=non_interactive,
            dry_run=dry_run,
            overwrite=overwrite,
            variable_resolver=variable_resolver,
        )
    except Exception as error:
        raise_cli_error(error)

    if isinstance(result, str):
        typer.echo(result)
        return

    typer.echo(result.format_summary())
