from pathlib import Path
from typing import Any

from mixy.models.base import BaseModel


class SourceMeta(BaseModel):
    src: Any
    src_type: str
    dest: Path = Path("/")
    other: dict[str, Any] = {}
