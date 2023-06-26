from pydantic import Field
from mixy.models.base import BaseModel


class PluginSettings(BaseModel):
    location: str = Field(...)
    active: bool = Field(True)
