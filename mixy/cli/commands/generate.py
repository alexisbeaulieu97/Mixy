"""Project generation command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from loguru import logger

from mixy.application.use_cases.generate_project import generate_project
from mixy.cli.errors import raise_cli_error
from mixy.domain.services import VariableResolver


def generate(
    config_path: Annotated[
        Path,
        typer.Argument(help="Path to the Mixy config file."),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Override the configured output directory."),
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
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show the plan without writing files."),
    ] = False,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite file conflicts regardless of the config conflict policy.",
        ),
    ] = False,
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

    logger.info("{}", result.format_summary())
