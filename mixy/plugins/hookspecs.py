from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pluggy

from mixy.constants import PLUGIN_PROJECT_NAME

if TYPE_CHECKING:
    from mixy.models.blueprint import Blueprint
    from mixy.models.source_meta import SourceMeta
    from mixy.models.template_var import TemplateVar
    from mixy.plugins.plugin_manager import PluginManager

hook_spec = pluggy.HookspecMarker(PLUGIN_PROJECT_NAME)


@hook_spec(firstresult=True)
def load_configuration(config_file: Path) -> dict[str, Any]:
    ...


@hook_spec(firstresult=True)
def fetch(
    source: SourceMeta, blueprint: Blueprint, plugin_master: PluginManager
) -> bool | None:
    ...


@hook_spec(firstresult=True)
def output() -> bool | None:
    ...


@hook_spec(firstresult=True)
def resolve(var_name: str, var_config: TemplateVar) -> Any | None:
    ...
