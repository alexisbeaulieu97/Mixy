from pathlib import Path
from pydantic import Field
from mixy.constants import PLUGINS_DEFAULT_PATH
from mixy.models.base import BaseModel
from mixy.settings.plugin_settings import PluginSettings


class PluginsSettings(BaseModel):
    location: Path = Field(PLUGINS_DEFAULT_PATH)
    plugins: list[PluginSettings] = Field([])
