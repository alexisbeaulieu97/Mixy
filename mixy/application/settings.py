"""Runtime-only application settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Mapping, Optional

from pydantic import BaseModel, Field, validator


class AppSettings(BaseModel):
    """Non-project runtime settings loaded from the process environment."""

    cache_root: Optional[Path] = None
    enabled_source_providers: List[str] = Field(default_factory=list)

    class Config:
        extra = "forbid"

    @validator("enabled_source_providers", pre=True)
    def _split_provider_list(cls, value):  # type: ignore[no-untyped-def]
        if value in (None, ""):
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, Iterable):
            return [str(item).strip() for item in value if str(item).strip()]
        return value

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "AppSettings":
        source = environ or os.environ
        return cls.parse_obj(
            {
                "cache_root": source.get("MIXY_CACHE_ROOT"),
                "enabled_source_providers": source.get(
                    "MIXY_ENABLED_SOURCE_PROVIDERS",
                    "",
                ),
            }
        )
