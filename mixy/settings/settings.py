from pathlib import Path
from typing import Self

from pydantic import BaseSettings

from mixy.constants import HOME, SETTINGS_FILE_TOML, SETTINGS_FILE_YAML
from mixy.merge_strategies import RecursiveMergeStrategy
from mixy.protocols.merge_strategy import MergeStrategy
from mixy.settings.cache_settings import CacheSettings
from mixy.settings.jinja_settings import JinjaSettings
from mixy.settings.logging_settings import LoggingSettings
from mixy.settings.sources import (
    toml_config_settings_source,
    yaml_config_settings_source,
)


class Settings(BaseSettings):
    logs: LoggingSettings = LoggingSettings()
    jinja: JinjaSettings = JinjaSettings()
    cache: CacheSettings = CacheSettings()

    @property
    def home(self) -> Path:
        return HOME

    def merge_with(
        self, data: Self, strategy: MergeStrategy = RecursiveMergeStrategy()
    ) -> None:
        strategy.merge(self, data)

    class Config:
        env_file_encoding = "utf-8"
        env_prefix = "mixy_"
        env_nested_delimiter = "__"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                toml_config_settings_source(HOME.joinpath(SETTINGS_FILE_TOML)),
                yaml_config_settings_source(HOME.joinpath(SETTINGS_FILE_YAML)),
                env_settings,
                file_secret_settings,
            )


settings = Settings()
