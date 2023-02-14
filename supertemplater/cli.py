import os
from pathlib import Path
from typing import Any

import typer
import yaml
from jinja2 import Environment, StrictUndefined

from supertemplater.constants import CONFIG_DEST, SUPERTEMPLATER_CONFIG
from supertemplater.context import Context
from supertemplater.exceptions import (MissingProjectConfigurationError,
                                       ProjectAlreadyExistsError)
from supertemplater.models import Config, Project
from supertemplater.models.config import config
from supertemplater.preloaded_resolver import PreloadedResolver
from supertemplater.prompt_resolver import PromptResolver
from supertemplater.protocols.variable_resolver import VariableResolver

app = typer.Typer(pretty_exceptions_show_locals=False)
logger = config.logging.get_logger(__name__)


def update_config(project_config: Config) -> None:
    config_location = Path(os.getenv(SUPERTEMPLATER_CONFIG, CONFIG_DEST))
    user_config = (
        Config.load(config_location) if config_location.is_file() else Config()
    )
    logger.info("Updating the context with user configuration if present")
    config.update(user_config)
    logger.info("Updating the context with project configuration")
    config.update(project_config)


def get_project(config_file: Path) -> Project:
    if not config_file.is_file():
        raise MissingProjectConfigurationError(config_file)

    logger.info(f"Reading the project from {config_file}")
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
    try:
        logger.info(f"Creating the project using: {project_file}")
        project = get_project(project_file)

        if force:
            logger.info("The force option was used, emptying the project")
            project.empty()

        if not project.is_empty:
            raise ProjectAlreadyExistsError(project.base_dir)

        update_config(project.config)
        ctx = Context(env=Environment(undefined=StrictUndefined, **config.jinja.dict()))

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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
