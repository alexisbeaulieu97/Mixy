from pathlib import Path
from typing import Self

from pydantic import BaseSettings

from supertemplater.constants import SETTINGS_FILE
from supertemplater.merge_strategies import RecursiveMergeStrategy
from supertemplater.protocols.merge_strategy import MergeStrategy
from supertemplater.utils import get_home

from .jinja_settings import JinjaSettings
from .logging_settings import LoggingSettings
from .settings_sources import yaml_config_settings_source


class Settings(BaseSettings):
    logs: LoggingSettings = LoggingSettings()
    jinja: JinjaSettings = JinjaSettings()

    @property
    def home(self) -> Path:
        return get_home()

    @property
    def logs_home(self) -> Path:
        return self.logs.logs_home

    @property
    def cache_home(self) -> Path:
        return self.home.joinpath("cache")

    @property
    def dependencies_home(self) -> Path:
        return self.cache_home.joinpath("dependencies")

    def merge_with(
        self, data: Self, strategy: MergeStrategy = RecursiveMergeStrategy()
    ) -> None:
        strategy.merge(self, data)

    class Config:
        env_file_encoding = "utf-8"
        env_prefix = "supertemplater_"
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
                yaml_config_settings_source(get_home().joinpath(SETTINGS_FILE)),
                env_settings,
                file_secret_settings,
            )


settings = Settings()
