"""Source provider protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mixy.domain.models import MaterializedSource, SourceDefinition


@runtime_checkable
class SourceProvider(Protocol):
    def can_handle(self, source: SourceDefinition) -> bool:
        """Return True when this provider can resolve the given source."""

    def resolve(self, source: SourceDefinition) -> MaterializedSource:
        """Resolve the source into a local materialized directory."""

    def fingerprint(self, source: SourceDefinition) -> str:
        """Return a stable fingerprint for the source."""
