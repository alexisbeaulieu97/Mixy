from pathlib import Path
from typing import Any

import tomllib

from mixy.plugins.builtin import hook_impl


@hook_impl
def load_configuration(config_file: Path) -> dict[str, Any] | None:
    if not (config_file.is_file() and config_file.suffix == ".toml"):
        return
    return tomllib.loads(config_file.read_text())
