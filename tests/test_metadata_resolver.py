from pathlib import Path

import pytest

from mixy.domain.enums import VariableType
from mixy.domain.exceptions import MetadataConflictError
from mixy.domain.models import TemplateMetadata
from mixy.domain.services import MetadataResolver


def test_scalar_inheritance_uses_nearest_scope() -> None:
    resolver = MetadataResolver(
        directory_scopes={
            Path("."): TemplateMetadata.model_validate(
                {"copy_mode": "render", "render": {"path_names": True}}
            ),
            Path("docs"): TemplateMetadata.model_validate(
                {"copy_mode": "raw", "render": {"path_names": False}}
            ),
        }
    )

    effective = resolver.resolve_for_file(
        Path("docs/guide.md"),
        Path("/tmp/source"),
        TemplateMetadata(),
    )

    assert effective.copy_mode == "raw"
    assert effective.render.path_names is False


def test_list_inheritance_supports_union_and_replace() -> None:
    resolver = MetadataResolver(
        directory_scopes={
            Path("."): TemplateMetadata.model_validate({"exclude": ["*.png"]}),
            Path("docs"): TemplateMetadata.model_validate(
                {
                    "include": {"items": ["*.md"], "_replace": True},
                    "exclude": ["*.jpg"],
                }
            ),
        }
    )

    effective = resolver.resolve_for_file(
        Path("docs/guide.md"),
        Path("/tmp/source"),
        TemplateMetadata(),
    )

    assert effective.include == ["*.md"]
    assert effective.exclude == ["*.png", "*.jpg"]


def test_map_inheritance_deep_merges_variables_and_defaults() -> None:
    resolver = MetadataResolver(
        directory_scopes={
            Path("."): TemplateMetadata.model_validate(
                {
                    "render": {"text_files": True, "path_names": True},
                    "variables": {"project_name": {"type": "str"}},
                    "defaults": {"project_name": "demo"},
                }
            ),
            Path("docs"): TemplateMetadata.model_validate(
                {
                    "render": {"path_names": False},
                    "variables": {"project_name": {"type": "str", "description": "Docs project"}},
                    "defaults": {"project_name": "docs-demo"},
                }
            ),
        }
    )

    effective = resolver.resolve_for_file(
        Path("docs/guide.md"),
        Path("/tmp/source"),
        TemplateMetadata(),
    )

    assert effective.render.text_files is True
    assert effective.render.path_names is False
    assert effective.variables["project_name"].type is VariableType.STR
    assert effective.variables["project_name"].description == "Docs project"
    assert effective.defaults["project_name"] == "docs-demo"


def test_variable_refinement_rejects_type_changes() -> None:
    resolver = MetadataResolver(
        directory_scopes={
            Path("."): TemplateMetadata.model_validate({"variables": {"port": {"type": "int"}}}),
            Path("docs"): TemplateMetadata.model_validate({"variables": {"port": {"type": "str"}}}),
        }
    )

    with pytest.raises(MetadataConflictError):
        resolver.resolve_for_file(
            Path("docs/guide.md"),
            Path("/tmp/source"),
            TemplateMetadata(),
        )


def test_variable_refinement_rejects_incompatible_choices() -> None:
    resolver = MetadataResolver(
        directory_scopes={
            Path("."): TemplateMetadata.model_validate(
                {"variables": {"color": {"type": "str", "choices": ["red", "blue"]}}}
            ),
            Path("docs"): TemplateMetadata.model_validate(
                {"variables": {"color": {"type": "str", "choices": ["green"]}}}
            ),
        }
    )

    with pytest.raises(MetadataConflictError):
        resolver.resolve_for_file(
            Path("docs/guide.md"),
            Path("/tmp/source"),
            TemplateMetadata(),
        )
