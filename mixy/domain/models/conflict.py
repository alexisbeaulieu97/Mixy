"""Conflict value objects for merge planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mixy.domain.enums import ConflictType


@dataclass(frozen=True)
class Conflict:
    path: Path
    source_a_id: str
    source_b_id: str
    type: ConflictType
