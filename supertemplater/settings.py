import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, BaseSettings

from supertemplater.constants import CONFIG_FILE, DEFAULT_HOME_DEST, SUPERTEMPLATER_HOME
from supertemplater.models.log_level import LogLevel
from supertemplater.utils import get_current_time

SETTINGS_HOME = Path(os.getenv(SUPERTEMPLATER_HOME, DEFAULT_HOME_DEST))


def yaml_config_settings_source(settings: BaseSettings) -> dict[str, Any]:
    location = SETTINGS_HOME.joinpath(CONFIG_FILE)
    if not location.is_file():
        return {}
    encoding = settings.__config__.env_file_encoding
    return yaml.safe_load(location.open(encoding=encoding))


class LoggingSettings(BaseModel):
    console_level: LogLevel = LogLevel.WARNING
    file_level: LogLevel = LogLevel.DEBUG
    file_dest_dir: Path = SETTINGS_HOME.joinpath("logs")
    file_name: str = f"{get_current_time().strftime('%Y-%m-%d_%H:%M:%S')}.log"
    logging_format: str = "%(asctime)s | %(name)s | %(levelname)s : %(message)s"

    @property
    def file_dest(self) -> Path:
        return Path(self.file_dest_dir, self.file_name)


class Settings(BaseSettings):
    logs: LoggingSettings = LoggingSettings()

    class Config:
        env_file_encoding = "utf-8"
        env_prefix = "supertemplater_"
        env_nested_delimiter = "_"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                yaml_config_settings_source,
                env_settings,
                file_secret_settings,
            )


settings = Settings()
