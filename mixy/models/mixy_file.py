from mixy.models.base import BaseModel
from mixy.models.template_var import TemplateVar


class MixyFile(BaseModel):
    content: str = ""
    vars: dict[str, TemplateVar] = {}
