from __future__ import annotations

from pathlib import Path

from mixy.models.blueprint import Blueprint
from mixy.models.source_meta import SourceMeta
from mixy.models.template import Template
from mixy.pathutil import get_directory_contents, join_relative_to_root
from mixy.plugins.builtin import hook_impl
from mixy.plugins.plugin_manager import plugin_master


@hook_impl(trylast=True)
def fetch(source: SourceMeta, blueprint: Blueprint) -> bool | None:
    if source.src_type != "directory" or not Path(source.src).is_dir():
        return
    src = Path(source.src)
    contents = get_directory_contents(src)
    for content in contents:
        plugin_master.hook.fetch(
            source=SourceMeta(
                src=content,
                src_type="directory" if content.is_dir() else "file",
                dest=join_relative_to_root(source.dest, content.relative_to(src)),
            ),
            blueprint=blueprint,
        )
    return True
