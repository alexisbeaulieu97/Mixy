from typing import Any

from mixy.models.base import BaseModel


class TemplateVar(BaseModel):
    description: str | None = None
    default: Any | None = None
    secret: bool = False
    resolver: str = "prompt"
