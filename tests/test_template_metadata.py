from pathlib import Path

import pytest

from mixy.domain.enums import VariableType
from mixy.domain.exceptions import MetadataValidationError
from mixy.domain.models import TemplateMetadata, VariableDefinition
from mixy.infrastructure.config import MetadataLoader


def test_template_metadata_accepts_allowed_fields() -> None:
    metadata = TemplateMetadata.model_validate(
        {
            "description": "docs",
            "copy_mode": "render",
            "render": {"undefined": "strict", "path_names": True, "text_files": False},
            "include": {"items": ["*.md"], "_replace": True},
            "exclude": ["*.png"],
            "defaults": {"project_name": "demo"},
            "variables": {
                "project_name": {
                    "type": "str",
                    "description": "Project name",
                }
            },
        }
    )

    assert metadata.copy_mode == "render"
    assert metadata.render is not None
    assert metadata.render.path_names is True
    assert metadata.include is not None
    assert metadata.include.items == ["*.md"]
    assert metadata.include.replace is True
    assert metadata.variables["project_name"] == VariableDefinition(
        type=VariableType.STR,
        description="Project name",
    )


def test_template_metadata_rejects_disallowed_fields(tmp_path: Path) -> None:
    metadata_path = tmp_path / ".mixy" / "template.yml"
    metadata_path.parent.mkdir()
    metadata_path.write_text("source:\n  type: local_dir\n", encoding="utf-8")

    with pytest.raises(MetadataValidationError) as error:
        MetadataLoader().discover(tmp_path)

    assert "Disallowed metadata field" in str(error.value)
    assert str(metadata_path) in str(error.value)
