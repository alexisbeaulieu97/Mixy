from pathlib import Path

from mixy.infrastructure.config import MetadataLoader


def test_discover_finds_directory_and_file_metadata(tmp_path: Path) -> None:
    source_root = tmp_path / "template"
    (source_root / ".mixy").mkdir(parents=True)
    (source_root / ".mixy" / "template.yml").write_text(
        "exclude:\n  - '*.png'\nvariables:\n  project_name:\n    type: str\n",
        encoding="utf-8",
    )
    (source_root / "src" / ".mixy").mkdir(parents=True)
    (source_root / "src" / ".mixy" / "template.yml").write_text(
        "defaults:\n  module_name: utils\n",
        encoding="utf-8",
    )
    (source_root / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    (source_root / "Dockerfile.mixy.yml").write_text(
        "copy_mode: raw\n",
        encoding="utf-8",
    )

    discovered = MetadataLoader().discover(source_root)

    assert discovered.directory_scopes[Path(".")].exclude is not None
    assert discovered.directory_scopes[Path("src")].defaults["module_name"] == "utils"
    assert discovered.file_scopes[Path("Dockerfile")].copy_mode == "raw"


def test_discover_returns_empty_when_no_metadata_present(tmp_path: Path) -> None:
    source_root = tmp_path / "template"
    source_root.mkdir()
    (source_root / "README.md").write_text("hello\n", encoding="utf-8")

    discovered = MetadataLoader().discover(source_root)

    assert discovered.directory_scopes == {}
    assert discovered.file_scopes == {}
