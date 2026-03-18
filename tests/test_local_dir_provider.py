from pathlib import Path

import pytest

from mixy.domain.exceptions import SourceResolutionError
from mixy.domain.models import LocalDirSource
from mixy.infrastructure.sources.base import SourceProvider
from mixy.infrastructure.sources.local import LocalDirProvider

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sources"


def test_local_dir_provider_resolves_existing_directory() -> None:
    provider = LocalDirProvider()

    materialized = provider.resolve(
        LocalDirSource(type="local_dir", path=FIXTURES_DIR / "base-template")
    )

    assert materialized.root_path == (FIXTURES_DIR / "base-template").resolve()
    assert materialized.root_path.is_absolute()
    assert materialized.metadata["provider"] == "local_dir"


def test_local_dir_provider_raises_for_missing_directory() -> None:
    provider = LocalDirProvider()

    with pytest.raises(SourceResolutionError):
        provider.resolve(LocalDirSource(type="local_dir", path=FIXTURES_DIR / "missing"))


def test_local_dir_provider_raises_for_file_path() -> None:
    provider = LocalDirProvider()

    with pytest.raises(SourceResolutionError):
        provider.resolve(LocalDirSource(type="local_dir", path=FIXTURES_DIR / "not-a-dir.txt"))


def test_local_dir_provider_supports_subpath_resolution() -> None:
    provider = LocalDirProvider()

    materialized = provider.resolve(
        LocalDirSource(type="local_dir", path=FIXTURES_DIR / "base-template", subpath="nested")
    )

    assert materialized.root_path == (FIXTURES_DIR / "base-template" / "nested").resolve()


def test_local_dir_provider_fingerprint_is_stable() -> None:
    provider = LocalDirProvider()
    source = LocalDirSource(type="local_dir", path=FIXTURES_DIR / "base-template")

    first = provider.fingerprint(source)
    second = provider.fingerprint(source)

    assert first == second


def test_local_dir_provider_satisfies_source_provider_protocol() -> None:
    provider = LocalDirProvider()

    assert isinstance(provider, SourceProvider)
