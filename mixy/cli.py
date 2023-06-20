from enum import Enum
from pathlib import Path
from typing import Any, Optional

import tomllib
import typer
import yaml
from jinja2 import Environment, StrictUndefined

from mixy.context import Context
from mixy.exceptions import MissingProjectConfigurationError, ProjectAlreadyExistsError
from mixy.logger_builder import LoggerBuilder
from mixy.models.project import Project
from mixy.preloaded_resolver import PreloadedResolver
from mixy.settings.project_settings import ProjectSettings
from mixy.settings.settings import settings
from mixy.utils import clear_directory

app = typer.Typer(pretty_exceptions_show_locals=False)
logger = LoggerBuilder.with_settings(settings.logs, __name__)


class SupportedConfigFormat(Enum):
    YAML = (".yaml", ".yml")
    TOML = ".toml"


def update_settings(project_settings: ProjectSettings) -> None:
    logger.info("Updating the settings with project settings")
    settings.jinja.merge_with(project_settings.jinja)


def load_file_data(config_file: Path) -> dict:
    if config_file.suffix in SupportedConfigFormat.YAML.value:
        with config_file.open() as file:
            return yaml.safe_load(file) or {}
    elif config_file.suffix == SupportedConfigFormat.TOML.value:
        return tomllib.loads(config_file.read_text()) or {}
    else:
        raise ValueError("Unsupported project configuration format.")


def validate_and_get_project(destination: Path, config_file: Path) -> Project:
    if not config_file.is_file():
        raise MissingProjectConfigurationError(config_file)

    logger.info(f"Reading the project from {config_file}")
    project_config = load_file_data(config_file)
    return Project(destination=destination, **project_config)


def check_and_empty_project(force: bool, project: Project) -> None:
    if force:
        logger.info("The force option was used, emptying the project")
        project.empty()

    if not project.is_empty:
        raise ProjectAlreadyExistsError(project.destination)


def create_project(project: Project, context: Optional[Path] = None) -> None:
    update_settings(project.settings)
    ctx = Context(env=Environment(undefined=StrictUndefined, **settings.jinja.dict()))

    if context is not None:
        logger.info(f"Importing the provided context: {context}")
        context_data: dict[str, Any] = yaml.safe_load(context.read_text()) or {}
        ctx.resolver = PreloadedResolver(context_data)

    logger.info("Creating the project")
    project.create(ctx)


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
) -> None:
    try:
        logger.info(f"Creating the project using: {project_file.absolute()}")
        project = validate_and_get_project(destination, project_file)
        check_and_empty_project(force, project)
        create_project(project, context)
        logger.info("Project creation complete")
    except (
        typer.Abort,
        MissingProjectConfigurationError,
        ProjectAlreadyExistsError,
    ) as e:
        logger.error(f"Project creation failed: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error occurred while creating project: {e}")

    if not settings.cache.enabled:
        logger.info("Cache is disabled, removing the cached dependencies")
        clear()


@app.command(help="Clear the program's cache.")
def clear() -> None:
    logger.info("Clearing the cache")
    clear_directory(settings.cache.location)
    logger.info("Cache cleared successfully")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
