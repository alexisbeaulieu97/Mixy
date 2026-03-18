"""Resolved source value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MaterializedSource:
    root_path: Path
    source_id: str
    fingerprint: str
    metadata: dict[str, str] = field(default_factory=dict)
