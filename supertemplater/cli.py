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
from supertemplater.prompts import PromptResolver

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

    return Project(**yaml.safe_load(config_file.open()))


def resolve_missing_variables(config: Project) -> dict[str, Any]:
    return config.variables.resolve(PromptResolver())


@app.command()
def create(project_file: Path):
    project = get_project(project_file)

    if not project.is_empty:
        # TODO handle error
        raise Exception

    update_config(project.config)
    context = Context(env=Environment(undefined=StrictUndefined, **config.jinja.dict()))
    context.update(**resolve_missing_variables(project))
    project = project.render(context)
    project.resolve_dependencies(context)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
