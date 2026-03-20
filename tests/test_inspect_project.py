from pathlib import Path

from mixy.application.use_cases.inspect_project import inspect_project


def test_inspect_project_reports_variable_provenance_and_preview(tmp_path: Path) -> None:
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md.j2").write_text("# {{ project_name }}\n", encoding="utf-8")

    config_path = tmp_path / "mixy.yml"
    config_path.write_text(
        'version: "1"\n'
        "variables:\n"
        "  project_name:\n"
        "    type: str\n"
        "    required: false\n"
        "    default: demo\n"
        "sources:\n"
        "  - id: base\n"
        "    source:\n"
        "      type: local_dir\n"
        f"      path: {template_dir}\n"
        "output:\n"
        f"  path: {tmp_path / 'generated'}\n",
        encoding="utf-8",
    )

    report = inspect_project(config_path)

    assert report.summary.name == "-"
    assert report.summary.version == "1"
    assert report.variables[0].value_source.value == "default"
    assert report.variables[0].value == "demo"
    assert report.sources[0].location == str(template_dir)
    assert report.merge_preview[0].source_id == "base"
    assert report.merge_preview[0].output_path.name == "README.md"
