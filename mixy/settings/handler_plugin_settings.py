from pathlib import Path

from pydantic import Field
from mixy.constants import HANDLER_PLUGINS_DEFAULT_PATH

from mixy.models.base import BaseModel


class HandlerPluginSettings(BaseModel):
    active: list[str] = Field([], description="List of active handler plugins")
    location: Path = Field(
        HANDLER_PLUGINS_DEFAULT_PATH,
        description="Location of the handler plugins",
    )
    default: dict[str, str] = Field(
        {},
        description="Mapping of default parser plugins",
    )
