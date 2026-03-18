from pathlib import Path

import pytest

from mixy.domain.exceptions import SourceResolutionError
from mixy.domain.models import (
    LocalDirSource,
    MaterializedSource,
    SourceDefinition,
    TemplateReference,
)
from mixy.domain.services import SourceResolver

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sources"


class StubLocalProvider:
    def __init__(self) -> None:
        self.seen_sources: list[SourceDefinition] = []

    def can_handle(self, source: SourceDefinition) -> bool:
        return source.type == "local_dir"

    def resolve(self, source: SourceDefinition) -> MaterializedSource:
        self.seen_sources.append(source)
        return MaterializedSource(
            root_path=Path("/tmp/materialized").resolve(),
            source_id="stub",
            fingerprint="fingerprint",
        )

    def fingerprint(self, source: SourceDefinition) -> str:
        return "fingerprint"


def test_source_resolver_dispatches_to_matching_provider() -> None:
    provider = StubLocalProvider()
    resolver = SourceResolver([provider])

    materialized = resolver.resolve(LocalDirSource(type="local_dir", path=FIXTURES_DIR))

    assert materialized.root_path == Path("/tmp/materialized").resolve()
    assert provider.seen_sources


def test_source_resolver_raises_on_missing_provider() -> None:
    resolver = SourceResolver()

    with pytest.raises(SourceResolutionError):
        resolver.resolve(LocalDirSource(type="local_dir", path=FIXTURES_DIR))


def test_resolve_all_uses_template_reference_id_and_subpath() -> None:
    provider = StubLocalProvider()
    resolver = SourceResolver([provider])

    materialized = resolver.resolve_all(
        [
            TemplateReference(
                id="base",
                subpath="nested",
                source=LocalDirSource(type="local_dir", path=FIXTURES_DIR / "base-template"),
            )
        ]
    )

    assert materialized[0].source_id == "base"
    assert provider.seen_sources[0].subpath == "nested"
