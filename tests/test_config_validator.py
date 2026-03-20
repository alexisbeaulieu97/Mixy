from pathlib import Path

import pytest
from pydantic import ValidationError

from mixy.domain.enums import VariableType
from mixy.domain.models import (
    LocalDirSource,
    ProjectDefinition,
    TemplateReference,
    VariableDefinition,
)
from mixy.domain.services.config_validator import validate


def test_validate_reports_duplicate_source_ids() -> None:
    definition = ProjectDefinition(
        version="1",
        sources=[
            TemplateReference(
                id="base",
                source=LocalDirSource(type="local_dir", path=Path("/tmp/one")),
            ),
            TemplateReference(
                id="base",
                source=LocalDirSource(type="local_dir", path=Path("/tmp/two")),
            ),
        ],
    )

    issues = validate(definition)

    assert any(
        issue.field_path == "sources[1].id" and issue.severity == "error" for issue in issues
    )


def test_variable_definition_rejects_default_type_mismatch() -> None:
    with pytest.raises(ValidationError):
        VariableDefinition(type=VariableType.INT, default="hello")


def test_variable_definition_rejects_choice_type_mismatch() -> None:
    with pytest.raises(ValidationError):
        VariableDefinition(type=VariableType.STR, choices=[1, 2])


def test_validate_errors_for_missing_local_source_path() -> None:
    definition = ProjectDefinition(
        version="1",
        sources=[
            TemplateReference(
                id="base",
                source=LocalDirSource(type="local_dir", path=Path("/definitely/missing/path")),
            )
        ],
    )

    issues = validate(definition)

    assert any(
        issue.field_path == "sources[0].source.path" and issue.severity == "error"
        for issue in issues
    )
