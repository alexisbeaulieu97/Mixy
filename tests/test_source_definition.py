import pytest
from pydantic import ValidationError, parse_obj_as

from mixy.domain.models import GitSource, LocalDirSource, SourceDefinition


def test_source_union_dispatches_by_type() -> None:
    local_dir = parse_obj_as(SourceDefinition, {"type": "local_dir", "path": "./templates"})
    git = parse_obj_as(
        SourceDefinition,
        {"type": "git", "url": "https://example.com/repo.git", "ref": "main"}
    )

    assert isinstance(local_dir, LocalDirSource)
    assert isinstance(git, GitSource)


def test_source_union_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        parse_obj_as(SourceDefinition, {"type": "s3_bucket", "bucket": "templates"})


def test_source_union_rejects_local_file() -> None:
    with pytest.raises(ValidationError):
        parse_obj_as(SourceDefinition, {"type": "local_file", "path": "./template.yml"})
