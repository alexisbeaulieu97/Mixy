import pytest
from pydantic import TypeAdapter, ValidationError

from mixy.domain.models import GitSource, LocalDirSource, SourceDefinition


def test_source_union_dispatches_by_type() -> None:
    adapter = TypeAdapter(SourceDefinition)

    local_dir = adapter.validate_python({"type": "local_dir", "path": "./templates"})
    git = adapter.validate_python(
        {"type": "git", "url": "https://example.com/repo.git", "ref": "main"}
    )

    assert isinstance(local_dir, LocalDirSource)
    assert isinstance(git, GitSource)


def test_source_union_rejects_unknown_type() -> None:
    adapter = TypeAdapter(SourceDefinition)

    with pytest.raises(ValidationError):
        adapter.validate_python({"type": "s3_bucket", "bucket": "templates"})


def test_source_union_rejects_local_file() -> None:
    adapter = TypeAdapter(SourceDefinition)

    with pytest.raises(ValidationError):
        adapter.validate_python({"type": "local_file", "path": "./template.yml"})
