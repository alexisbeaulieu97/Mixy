from pathlib import Path
from typing import Any

import typer
from jinja2 import Environment, StrictUndefined

from mixy.logger_builder import LoggerBuilder
from mixy.models.blueprint import Blueprint
from mixy.models.project import Project
from mixy.models.template import Template
from mixy.models.template_var import TemplateVar
from mixy.pathutil import clear_directory, is_empty_directory, load_configuration_file
from mixy.plugins.plugin_manager import plugin_master
from mixy.settings import user_settings
from mixy.settings.project_settings import ProjectSettings
from mixy.vars_manager import VarsManager

app = typer.Typer(pretty_exceptions_show_locals=False)
logger = LoggerBuilder.with_settings(user_settings.logs, __name__)


def update_settings(project_settings: ProjectSettings) -> None:
    logger.info("Updating the settings with project settings")
    user_settings.jinja.merge_with(project_settings.jinja)


def get_project(config_file: Path, destination: Path) -> Project:
    logger.info(f"Reading the project from {config_file}")
    project_config = load_configuration_file(config_file)
    return Project(destination=destination, **project_config)


def prepare_destination(destination: Path, force: bool) -> None:
    if destination.is_dir() and not is_empty_directory(destination):
        if force:
            logger.info("The force option was used, emptying the project")
            clear_directory(destination)
        else:
            raise FileExistsError(
                "The project already exists. "
                f'Please empty "{destination.absolute()}" or use the -f/--force option'
            )
    if not destination.is_dir():
        destination.mkdir()


@app.command(help="Create a new project.")
def create(
    project_file: Path = typer.Argument(
        ...,
        show_default=False,
        exists=True,
        dir_okay=False,
        help="The project's configuration file.",
    ),
    destination: Path = typer.Argument(
        ...,
        show_default=False,
        file_okay=False,
        help="The project's destination directory. Must be empty.",
    ),
    context: Path = typer.Option(
        None,
        "--context",
        "-c",
        dir_okay=False,
        show_default=False,
        writable=True,
        help="Use a configuration file to resolve the project variables.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite the project if it already exists.",
    ),
) -> None:
    try:
        logger.info(f"Creating the project using: {project_file.absolute()}")
        prepare_destination(destination, force)

        project = get_project(project_file, destination)
        update_settings(project.settings)

        blueprints = project.create()
        global_scope = VarsManager(vars=project.vars)
        if context is not None:
            context_values: dict[
                str, Any
            ] | None = plugin_master.hook.load_configuration(config_file=context)
            if context_values is not None:
                global_scope.add_values(**context_values)
        for b in blueprints:
            b.add_scope(Path("/"), global_scope)
            b.build(
                project.destination,
                environment=Environment(
                    undefined=StrictUndefined,
                    **user_settings.jinja.dict(),
                ),
            )
        logger.info("Project creation complete")
    except typer.Abort:
        logger.error("Project creation aborted")
    except Exception as e:
        logger.exception(f"Unexpected error occurred while creating project: {e}")

    if not user_settings.cache.enabled:
        logger.info("Cache is disabled, removing the cached dependencies")
        clear()


@app.command(help="Clear the program's cache.")
def clear() -> None:
    logger.info("Clearing the cache")
    clear_directory(user_settings.cache.location)
    logger.info("Cache cleared successfully")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
