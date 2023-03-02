from pathlib import Path
from typing import Any

import typer
import yaml
from jinja2 import Environment, StrictUndefined

from supertemplater.builders.logger_builder import LoggerBuilder
from supertemplater.context import Context
from supertemplater.exceptions import (MissingProjectConfigurationError,
                                       ProjectAlreadyExistsError)
from supertemplater.models import Project
from supertemplater.preloaded_resolver import PreloadedResolver
from supertemplater.prompt_resolver import PromptResolver
from supertemplater.protocols.variable_resolver import VariableResolver
from supertemplater.settings import Settings, settings
from supertemplater.utils import clear_directory, get_home

app = typer.Typer(pretty_exceptions_show_locals=False)
logger = LoggerBuilder.with_settings(settings.logs, __name__)


def update_settings(project_settings: Settings) -> None:
    logger.info("Updating the settings with project settings")
    settings.update(project_settings)


def get_project(destination: Path, config_file: Path) -> Project:
    if not config_file.is_file():
        raise MissingProjectConfigurationError(config_file)

    logger.info(f"Reading the project from {config_file}")
    project_config = yaml.safe_load(config_file.open()) or {}
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


@app.command(help="Clear the program cache.")
def clear():
    clear_directory(settings.cache_home)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
