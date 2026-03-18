"""Application service for source provider dispatch and materialization."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from mixy.application.ports import SourceProvider
from mixy.domain.exceptions import SourceResolutionError
from mixy.domain.models import MaterializedSource, SourceDefinition, TemplateReference


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
            try:
                if not reference.enabled:
                    continue
                source = _apply_reference_subpath(reference)
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
                        **({"alias": reference.alias} if reference.alias is not None else {}),
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
            suggestion="Use one of the supported source types: local_dir, git.",
        )


def _apply_reference_subpath(reference: TemplateReference) -> SourceDefinition:
    source = reference.source

    if reference.subpath is None:
        return source

    if source.type != "local_dir":
        raise SourceResolutionError(
            "Reference-level subpath is only supported for local_dir sources; "
            "use source.subpath for git sources.",
            suggestion="Move the subpath to source.subpath for git sources.",
        )

    return source.model_copy(update={"subpath": reference.subpath})
