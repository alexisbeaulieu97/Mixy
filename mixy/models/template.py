from mixy.models.base import BaseModel
from mixy.models.field_types import AbsolutePath


class Template(BaseModel):
    destination: AbsolutePath
    content: str | bytes
