from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mixy.models.template import Template
from mixy.plugins.builtin import hook_impl

if TYPE_CHECKING:
    from mixy.models.blueprint import Blueprint
    from mixy.models.source_meta import SourceMeta
    from mixy.plugins.plugin_manager import PluginManager


@hook_impl(trylast=True)
def fetch(
    source: SourceMeta, blueprint: Blueprint, plugin_master: PluginManager
) -> bool | None:
    if source.src_type != "file" or not Path(source.src).is_file():
        return
    src = Path(source.src)
    try:
        content = src.read_text()
    except UnicodeDecodeError:
        content = src.read_bytes()

    blueprint.add_template(
        Template(
            destination=source.dest,
            content=content,
        ),
    )
    return True
