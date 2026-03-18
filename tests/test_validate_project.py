import importlib
from pathlib import Path

from mixy.application.use_cases.validate_project import validate_project
from mixy.domain.models import ProjectDefinition
from mixy.domain.services import ValidationIssue


def test_validate_project_loads_and_validates_config(tmp_path: Path) -> None:
    config_path = tmp_path / "mixy.yml"
    config_path.write_text('version: "1"\nsources: []\n', encoding="utf-8")
    seen_paths: list[Path] = []
    seen_definition: list[ProjectDefinition] = []

    def config_loader(path: Path) -> ProjectDefinition:
        seen_paths.append(path)
        return ProjectDefinition(version="1", sources=[])

    def config_validator(definition: ProjectDefinition) -> list[ValidationIssue]:
        seen_definition.append(definition)
        return [ValidationIssue(severity="warning", field_path="sources", message="ok")]

    issues = validate_project(
        config_path,
        config_loader=config_loader,
        config_validator=config_validator,
    )

    assert seen_paths == [config_path]
    assert seen_definition == [ProjectDefinition(version="1", sources=[])]
    assert issues == [
        ValidationIssue(severity="warning", field_path="sources", message="ok")
    ]


def test_validate_project_uses_composed_default_config_loader(monkeypatch) -> None:
    validate_module = importlib.import_module("mixy.application.use_cases.validate_project")
    seen_paths: list[Path] = []
    seen_definition: list[ProjectDefinition] = []

    def config_loader(path: Path) -> ProjectDefinition:
        seen_paths.append(path)
        return ProjectDefinition(version="1", sources=[])

    def config_validator(definition: ProjectDefinition) -> list[ValidationIssue]:
        seen_definition.append(definition)
        return []

    monkeypatch.setattr(validate_module, "build_config_loader", lambda loader=None: config_loader)

    config_path = Path("mixy.yml")
    issues = validate_module.validate_project(config_path, config_validator=config_validator)

    assert issues == []
    assert seen_paths == [config_path]
    assert seen_definition == [ProjectDefinition(version="1", sources=[])]
