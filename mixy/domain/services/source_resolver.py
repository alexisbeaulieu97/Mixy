"""Source provider dispatch and source materialization."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from mixy.domain.exceptions import SourceResolutionError
from mixy.domain.models import MaterializedSource, SourceDefinition, TemplateReference
from mixy.infrastructure.sources.base import SourceProvider


class SourceResolver:
    """Resolve abstract source definitions through registered providers."""

    def __init__(self, providers: Iterable[SourceProvider] | None = None) -> None:
        self._providers = list(providers or [])

    def register(self, provider: SourceProvider) -> None:
        self._providers.append(provider)

    def list_providers(self) -> list[SourceProvider]:
        return list(self._providers)

    def resolve(self, source: SourceDefinition) -> MaterializedSource:
        provider = self._find_provider(source)
        return provider.resolve(source)

    def resolve_all(self, sources: list[TemplateReference]) -> list[MaterializedSource]:
        materialized: list[MaterializedSource] = []

        for reference in sources:
            source = _apply_reference_subpath(reference)
            try:
                resolved = self.resolve(source)
            except SourceResolutionError as error:
                raise SourceResolutionError(
                    str(error),
                    source_id=reference.id,
                    suggestion=error.suggestion,
                    system_error=error.system_error,
                ) from error
            materialized.append(
                replace(
                    resolved,
                    source_id=reference.id,
                    metadata={
                        **resolved.metadata,
                        "alias": reference.alias or "",
                        "enabled": str(reference.enabled).lower(),
                    },
                )
            )

        return materialized

    def _find_provider(self, source: SourceDefinition) -> SourceProvider:
        for provider in self._providers:
            if provider.can_handle(source):
                return provider

        raise SourceResolutionError(
            f'No source provider available for type "{source.type}".',
            suggestion="Use one of the supported source types: local_dir, local_file, git.",
        )


def _apply_reference_subpath(reference: TemplateReference) -> SourceDefinition:
    source = reference.source

    if source.type != "local_dir" or reference.subpath is None:
        return source

    return source.model_copy(update={"subpath": reference.subpath})
