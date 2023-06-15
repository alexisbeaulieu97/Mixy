from typing import Any, Optional

from mixy.models.base import RenderableBaseModel


class TemplateVar(RenderableBaseModel):
    description: Optional[str]
    default: Optional[Any]
    secret: bool = False
