from pathlib import Path

from mixy.domain.enums import ConflictPolicy, VariableType
from mixy.domain.models import (
    LocalDirSource,
    OutputDefinition,
    ProjectDefinition,
    TemplateReference,
    VariableDefinition,
)


def test_variable_definition_defaults() -> None:
    variable = VariableDefinition(type=VariableType.STR)

    assert variable.required is True
    assert variable.secret is False
    assert variable.default is None


def test_output_definition_defaults_to_fail_policy() -> None:
    output = OutputDefinition(path=Path("/tmp/output"))

    assert output.conflict_policy is ConflictPolicy.FAIL


def test_project_definition_valid_construction() -> None:
    definition = ProjectDefinition(
        version="1",
        name="demo",
        description="demo config",
        variables={"project_name": VariableDefinition(type=VariableType.STR)},
        values={"project_name": "demo"},
        sources=[
            TemplateReference(
                id="base",
                source=LocalDirSource(type="local_dir", path=Path("/tmp/templates")),
            )
        ],
        output=OutputDefinition(path=Path("/tmp/output")),
    )

    assert definition.version == "1"
    assert definition.sources[0].enabled is True
    assert definition.values["project_name"] == "demo"
