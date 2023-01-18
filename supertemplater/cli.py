import logging
import os
from pathlib import Path
from typing import Any, Optional

import typer
import yaml
from jinja2 import Environment, StrictUndefined
from rich.console import Console

from supertemplater.constants import CONFIG, SUPERTEMPLATER_CONFIG
from supertemplater.context import Context
from supertemplater.models import Config, Project
from supertemplater.models.config import config
from supertemplater.prompts import PromptResolver

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
        # TODO handle error
        raise Exception

    project_config = yaml.safe_load(config_file.open()) or {}

    return Project(**project_config)


def resolve_missing_variables(config: Project) -> dict[str, Any]:
    return config.variables.resolve(PromptResolver())


@app.command()
def create(project_file: Path, context: Optional[Path] = None, force: Optional[bool] = False):
    project = get_project(project_file)
    if force:
        project.empty()

    if not project.is_empty:
        # TODO handle error
        raise Exception("The project is not empty. Please empty it or use the --force option.")

    update_config(project.config)
    ctx = Context(env=Environment(undefined=StrictUndefined, **config.jinja.dict()))

    if context is not None:
        context_data: dict[str, Any] = yaml.safe_load(context.read_text()) or {}
        ctx.update(**context_data)
    else:
        ctx.update(**resolve_missing_variables(project))
    project = project.render(ctx)
    project.resolve_dependencies(ctx)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
