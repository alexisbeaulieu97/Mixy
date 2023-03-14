from pathlib import Path

from supertemplater.constants import CACHE_DEFAULT_PATH
from supertemplater.models.base import BaseModel


class CacheSettings(BaseModel):
    location: Path = CACHE_DEFAULT_PATH
    enabled: bool = True
