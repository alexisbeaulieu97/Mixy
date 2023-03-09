from supertemplater.models.base import BaseModel
from supertemplater.settings.jinja_settings import JinjaSettings


class ProjectSettings(BaseModel):
    jinja: JinjaSettings = JinjaSettings()
