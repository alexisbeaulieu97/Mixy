from pathlib import Path
from typing import Any

import yaml

from mixy.plugins.builtin import hook_impl


@hook_impl
def load_configuration(config_file: Path) -> dict[str, Any] | None:
    if not (config_file.is_file() and config_file.suffix in (".yaml", ".yml")):
        return
    return yaml.safe_load(config_file.read_text())
