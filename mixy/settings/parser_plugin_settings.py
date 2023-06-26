from pathlib import Path

from pydantic import Field
from mixy.constants import PARSER_PLUGINS_DEFAULT_PATH

from mixy.models.base import BaseModel


class ParserPluginSettings(BaseModel):
    active: list[str] = Field([], description="List of active parser plugins")
    location: Path = Field(
        PARSER_PLUGINS_DEFAULT_PATH,
        description="Location of the parser plugins",
    )
    default: dict[str, str] = Field(
        {},
        description="Mapping of default parser plugins",
    )
