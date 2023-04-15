from pathlib import Path
from typing import Any

import tomllib
import typer
import yaml
from jinja2 import Environment, StrictUndefined

from mixy.builders.logger_builder import LoggerBuilder
from mixy.context import Context
from mixy.exceptions import (
    MissingProjectConfigurationError,
    ProjectAlreadyExistsError,
)
from mixy.models.project import Project
from mixy.preloaded_resolver import PreloadedResolver
from mixy.prompt_resolver import PromptResolver
from mixy.protocols.variable_resolver import VariableResolver
from mixy.settings.project_settings import ProjectSettings
from mixy.settings.settings import settings
from mixy.utils import clear_directory

app = typer.Typer(pretty_exceptions_show_locals=False)
logger = LoggerBuilder.with_settings(settings.logs, __name__)


def update_settings(project_settings: ProjectSettings) -> None:
    logger.info("Updating the settings with project settings")
    settings.jinja.merge_with(project_settings.jinja)


def get_project(destination: Path, config_file: Path) -> Project:
    if not config_file.is_file():
        raise MissingProjectConfigurationError(config_file)

    logger.info(f"Reading the project from {config_file}")
    if config_file.suffix in (".yaml", ".yml"):
        project_config = yaml.safe_load(config_file.open()) or {}
    elif config_file.suffix == ".toml":
        project_config = tomllib.loads(config_file.read_text()) or {}
    else:
        # TODO make this a custom exception
        raise Exception("Unsupported project configuration format.")
    return Project(destination=destination, **project_config)


def resolve_missing_variables(
    config: Project, resolver: VariableResolver
) -> dict[str, Any]:
    return config.variables.resolve(resolver)


@app.command(help="Create a new project.")
def create(
    project_file: Path,
    destination: Path,
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
    try:
        logger.info(f"Creating the project using: {project_file.absolute()}")
        project = get_project(destination, project_file)
        project.destination = destination

        if force:
            logger.info("The force option was used, emptying the project")
            project.empty()

        if not project.is_empty:
            raise ProjectAlreadyExistsError(project.destination)

        update_settings(project.settings)
        ctx = Context(
            env=Environment(undefined=StrictUndefined, **settings.jinja.dict())
        )

        if context is not None:
            logger.info(f"Importing the provided context: {context}")
            context_data: dict[str, Any] = yaml.safe_load(context.read_text()) or {}
            ctx.update(
                **resolve_missing_variables(project, PreloadedResolver(context_data))
            )
        else:
            logger.info("Resolving missing variables")
            ctx.update(**resolve_missing_variables(project, PromptResolver()))

        logger.info("Rendering the project")
        project = project.render(ctx)

        logger.info("Resolving dependencies")
        project.resolve_dependencies(ctx)

        logger.info("Project creation complete")
    except typer.Abort as e:
        raise e
    except Exception:
        logger.exception("Project creation failed")

    if not settings.cache.enabled:
        logger.info("Cache is disabled, removing the cached dependencies")
        clear()


@app.command(help="Clear the program's cache.")
def clear():
    logger.info("Clearing the cache")
    clear_directory(settings.cache.location)
    logger.info("Cache cleared successfully")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
