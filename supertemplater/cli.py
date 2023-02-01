import logging
import os
from pathlib import Path
from typing import Any

import typer
import yaml
from jinja2 import Environment, StrictUndefined
from rich.console import Console

from supertemplater.constants import CONFIG, SUPERTEMPLATER_CONFIG
from supertemplater.context import Context
from supertemplater.models import Config, Project
from supertemplater.models.config import config
from supertemplater.prompt_resolver import PromptResolver
from supertemplater.exceptions import (
    ProjectAlreadyExistsError,
    MissingProjectConfigurationError,
)
from supertemplater.protocols.variable_resolver import VariableResolver
from supertemplater.preloaded_resolver import PreloadedResolver

logger = logging.getLogger(__name__)

app = typer.Typer(pretty_exceptions_show_locals=False)
console = Console()
err_console = Console(stderr=True)


def update_config(project_config: Config) -> None:
    config_location = Path(os.getenv(SUPERTEMPLATER_CONFIG, CONFIG))
    user_config = (
        Config.load(config_location) if config_location.is_file() else Config()
    )
    config.update(user_config)
    config.update(project_config)


def get_project(config_file: Path) -> Project:
    if not config_file.is_file():
        raise MissingProjectConfigurationError(config_file)

    project_config = yaml.safe_load(config_file.open()) or {}

    return Project(**project_config)


def resolve_missing_variables(
    config: Project, resolver: VariableResolver
) -> dict[str, Any]:
    return config.variables.resolve(resolver)


@app.command()
def create(
    project_file: Path,
    context: Path = typer.Option(
        None,
        "--context",
        "-c",
        help="Use a YAML file to resolve the project variables.",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite the project if it already exists."
    ),
):
    project = get_project(project_file)
    if force:
        project.empty()

    if not project.is_empty:
        raise ProjectAlreadyExistsError(project.base_dir)

    update_config(project.config)
    ctx = Context(env=Environment(undefined=StrictUndefined, **config.jinja.dict()))

    if context is not None:
        context_data: dict[str, Any] = yaml.safe_load(context.read_text()) or {}
        ctx.update(
            **resolve_missing_variables(project, PreloadedResolver(context_data))
        )
    else:
        ctx.update(**resolve_missing_variables(project, PromptResolver()))
    project = project.render(ctx)
    project.resolve_dependencies(ctx)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
