"""Application-owned dependency contracts for planning and generation."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Protocol, TypeAlias, runtime_checkable

from mixy.application.ports.source_provider import SourceProvider
from mixy.domain.models import ProjectDefinition
from mixy.domain.services import MetadataResolver

ConfigLoader: TypeAlias = Callable[[Path], ProjectDefinition]
VarsFileLoader: TypeAlias = Callable[[Path], dict[str, object]]
MetadataResolverFactory: TypeAlias = Callable[[Path], MetadataResolver]
SecretMasker: TypeAlias = Callable[[Iterable[str]], None]


@runtime_checkable
class SourceProviderRegistry(Protocol):
    def list_providers(self) -> list[SourceProvider]:
        """Return the source providers available to planning/generation."""
