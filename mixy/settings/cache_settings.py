from pathlib import Path

from mixy.constants import CACHE_DEFAULT_PATH
from mixy.models.base import BaseModel


class CacheSettings(BaseModel):
    location: Path = CACHE_DEFAULT_PATH
    enabled: bool = True
