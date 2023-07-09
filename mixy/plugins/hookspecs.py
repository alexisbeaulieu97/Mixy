from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pluggy

from mixy.constants import PLUGIN_PROJECT_NAME

if TYPE_CHECKING:
    from mixy.models.blueprint import Blueprint
    from mixy.models.source_meta import SourceMeta
    from mixy.models.template_var import TemplateVar

hook_spec = pluggy.HookspecMarker(PLUGIN_PROJECT_NAME)


@hook_spec(firstresult=True)
def load_configuration(config_file: Path) -> dict[str, Any]:
    ...


@hook_spec(firstresult=True)
def fetch(source: SourceMeta, blueprint: Blueprint) -> bool | None:
    ...


# TODO to be decided
@hook_spec(firstresult=True)
def parse() -> None:
    ...


# TODO to be decided
@hook_spec(firstresult=True)
def handle() -> None:
    ...


@hook_spec(firstresult=True)
def resolve(var_name: str, var_config: TemplateVar) -> Any:
    ...
