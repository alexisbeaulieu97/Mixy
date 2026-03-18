from pathlib import Path

from mixy.application.use_cases.generate_project import generate_project
from mixy.application.use_cases.plan_project import plan_project
from mixy.domain.models import TemplateMetadata
from mixy.domain.services import MetadataResolver
from mixy.infrastructure.config import MetadataLoader

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "metadata"


def test_effective_metadata_resolves_across_root_directory_and_file_scopes() -> None:
    source_root = FIXTURES_DIR / "recursive"
    discovered = MetadataLoader().discover(source_root)
    resolver = MetadataResolver(discovered.directory_scopes, discovered.file_scopes)

    effective = resolver.resolve_for_file(
        Path("docs/guide.md"),
        source_root,
        TemplateMetadata(),
    )

    assert effective.copy_mode == "raw"
    assert effective.render.path_names is False
    assert effective.include == ["*.md"]
    assert effective.exclude == ["*.png"]
    assert effective.variables["project_name"].description == "Documentation project name"
    assert effective.variables["color"].choices == ["red"]
    assert effective.defaults["docs_title"] == "Reference"


def test_generate_project_applies_recursive_metadata_and_excludes_metadata_files(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        'version: "1"\n'
        "sources:\n"
        "  - id: recursive\n"
        "    source:\n"
        "      type: local_dir\n"
        f"      path: {FIXTURES_DIR / 'recursive'}\n"
        "output:\n"
        f"  path: {tmp_path / 'out'}\n",
        encoding="utf-8",
    )

    result = generate_project(
        config_path,
        var_overrides={"project_name": "mixy-demo"},
        non_interactive=True,
    )
    planned = plan_project(
        config_path,
        var_overrides={"project_name": "mixy-demo"},
        non_interactive=True,
    )
    decision = planned.prepared.render_decisions[("recursive", "docs/guide.md")]

    assert (tmp_path / "out" / "README.md").read_text(encoding="utf-8") == "# mixy-demo\n"
    assert (tmp_path / "out" / "docs" / "index.md").read_text(encoding="utf-8") == (
        "# Reference\nColor: red\n"
    )
    assert (tmp_path / "out" / "docs" / "guide.md").read_text(encoding="utf-8") == (
        "Guide for {{ project_name }}\n"
    )
    assert not (tmp_path / "out" / ".mixy").exists()
    assert not (tmp_path / "out" / "docs" / "guide.md.mixy.yml").exists()
    assert result.output_path == tmp_path / "out"
    assert decision.rendered is False
    assert decision.output_relative_path == Path("docs/guide.md")
