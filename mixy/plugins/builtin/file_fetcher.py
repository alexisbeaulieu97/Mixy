from __future__ import annotations

from pathlib import Path

from mixy.models.blueprint import Blueprint
from mixy.models.source_meta import SourceMeta
from mixy.models.template import Template
from mixy.plugins.builtin import hook_impl


@hook_impl(trylast=True)
def fetch(source: SourceMeta, blueprint: Blueprint) -> bool | None:
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
