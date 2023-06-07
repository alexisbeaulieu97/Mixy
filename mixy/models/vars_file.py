from mixy.models.base import RenderableBaseModel
from mixy.models.template_var_config import TemplateVarConfig


class VarsFile(RenderableBaseModel):
    variables: dict[str, TemplateVarConfig] = {}
