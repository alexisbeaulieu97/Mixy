from .base import RenderableBaseModel
from .template_var import TemplateVar


class MixyFile(RenderableBaseModel):
    content: str = ""
    vars: dict[str, TemplateVar] = {}
