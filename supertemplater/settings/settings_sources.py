from pathlib import Path
from typing import Any, Callable

import yaml
from pydantic import BaseSettings


def yaml_config_settings_source(
    location: Path,
) -> Callable[[BaseSettings], dict[str, Any]]:
    def getter(settings: BaseSettings) -> dict[str, Any]:
        if not location.is_file():
            return {}
        encoding = settings.__config__.env_file_encoding
        return yaml.safe_load(location.open(encoding=encoding))

    return getter
