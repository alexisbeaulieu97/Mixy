from mixy.models.base import BaseModel
from mixy.settings.jinja_settings import JinjaSettings


class ProjectSettings(BaseModel):
    jinja: JinjaSettings = JinjaSettings()
