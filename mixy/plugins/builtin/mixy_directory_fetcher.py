from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import tomllib

from mixy.models.blueprint import Blueprint
from mixy.vars_manager import VarsManager

if TYPE_CHECKING:
    from mixy.models.source_meta import SourceMeta

from mixy.plugins.builtin import hook_impl


@hook_impl
def fetch(source: SourceMeta, blueprint: Blueprint) -> bool | None:
    src = Path(source.src)
    if source.src_type != "directory" or not src.is_dir() or src.name != ".mixy":
        return

    vars_file = src / "vars.toml"

    if not vars_file.exists():
        return

    mixy_vars = tomllib.loads(vars_file.read_text())
    blueprint.add_scope(
        scope_path=source.dest.parent,
        scope=VarsManager(vars=mixy_vars),
    )
    return True
