"""Typer application entry point for Mixy."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

import typer
from loguru import logger

from mixy import get_version
from mixy.cli.commands import create_cache_app, generate, inspect_config, validate_config
from mixy.infrastructure.logging import configure_logging


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(create_cache_app(), name="cache")
app.command("generate")(generate)
app.command("validate")(validate_config)
app.command("inspect")(inspect_config)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    log_level: Annotated[
        LogLevel,
        typer.Option(
            "--log-level",
            case_sensitive=False,
            help="Set the minimum log level for Mixy output.",
        ),
    ] = LogLevel.INFO,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            help="Only show warnings and errors.",
        ),
    ] = False,
) -> None:
    """Run the Mixy CLI."""
    effective_log_level = LogLevel.WARNING if quiet else log_level
    configure_logging(effective_log_level.value)
    logger.debug("Configured logging at {} level.", effective_log_level.value)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def version() -> None:
    """Print the installed Mixy version."""
    resolved_version = get_version()
    logger.debug("Resolved Mixy version {}.", resolved_version)
    typer.echo(resolved_version)
