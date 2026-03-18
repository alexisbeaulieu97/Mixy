from pathlib import Path

import pytest

from mixy.domain.exceptions import ConfigValidationError, UnsupportedVersionError
from mixy.infrastructure.config import load_config

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "configs"


def test_load_minimal_config() -> None:
    definition = load_config(FIXTURES_DIR / "minimal.yml")

    assert definition.version == "1"
    assert len(definition.sources) == 1
    assert definition.sources[0].source.path == (FIXTURES_DIR / "templates" / "base").resolve()


def test_load_full_config() -> None:
    definition = load_config(FIXTURES_DIR / "full.yml")

    assert definition.name == "demo-project"
    assert definition.output is not None
    assert definition.output.path == (FIXTURES_DIR / "out").resolve()
    assert definition.sources[1].source.path == (FIXTURES_DIR / "templates" / "README.md").resolve()


def test_missing_version_raises_config_validation_error() -> None:
    with pytest.raises(ConfigValidationError) as error:
        load_config(FIXTURES_DIR / "missing_version.yml")

    assert error.value.field_path == "version"


def test_unknown_version_raises_unsupported_version_error() -> None:
    with pytest.raises(UnsupportedVersionError):
        load_config(FIXTURES_DIR / "unknown_version.yml")


def test_relative_paths_resolve_against_config_parent() -> None:
    definition = load_config(FIXTURES_DIR / "minimal.yml")

    resolved_path = definition.sources[0].source.path
    assert resolved_path == (FIXTURES_DIR / "templates" / "base").resolve()
