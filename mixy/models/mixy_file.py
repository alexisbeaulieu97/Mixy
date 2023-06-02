from mixy.models.template_var_config import TemplateVarConfig

from .base import RenderableBaseModel


class MixyFile(RenderableBaseModel):
    variables: dict[str, TemplateVarConfig]
    content: str
