import os
from pathlib import Path
from typing import Self

import yaml

from supertemplater.constants import HOME, SUPERTEMPLATER_HOME

from .base import RenderableBaseModel
from .jinja_config import JinjaConfig


class Config(RenderableBaseModel):
    """Config model."""

    _RENDERABLE_EXCLUDES = {"jinja"}

    # TODO add user config
    home: Path = Path(os.getenv(SUPERTEMPLATER_HOME, HOME))
    jinja: JinjaConfig = JinjaConfig()

    @classmethod
    def load(cls, config_file: Path) -> Self:
        """Load config from file."""
        config = yaml.safe_load(config_file.open())
        return cls(**config)

    def update(self, config: Self) -> None:
        self.home = config.home
        self.jinja = config.jinja


config = Config()
