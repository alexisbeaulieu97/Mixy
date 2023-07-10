from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import tomllib

from mixy.models.mixy_file import MixyFile
from mixy.models.template import Template
from mixy.plugins.builtin import hook_impl
from mixy.vars_manager import VarsManager

if TYPE_CHECKING:
    from mixy.models.blueprint import Blueprint
    from mixy.models.source_meta import SourceMeta


@hook_impl
def fetch(source: SourceMeta, blueprint: Blueprint) -> bool | None:
    src = Path(source.src)
    if source.src_type != "file" or not src.is_file() or src.suffix != ".mixy":
        return

    mixy_obj = tomllib.loads(src.read_text())
    mixy_file = MixyFile(**mixy_obj)

    blueprint.add_template(
        Template(
            destination=source.dest.with_suffix(""),
            content=mixy_file.content,
        ),
    )

    blueprint.add_scope(
        scope_path=source.dest.with_suffix(""),
        scope=VarsManager(vars=mixy_file.vars),
    )

    return True
