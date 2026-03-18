import importlib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mixy import get_version
from mixy.cli.app import app
from mixy.domain.exceptions import SourceResolutionError

E2E_DIR = Path(__file__).parent / "fixtures" / "e2e"


def test_version_command_outputs_package_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == get_version()


def test_help_returns_zero(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Usage" in result.stdout
    assert "generate" in result.stdout
    assert "validate" in result.stdout
    assert "inspect" in result.stdout


def test_generate_help_shows_all_options(runner: CliRunner) -> None:
    result = runner.invoke(app, ["generate", "--help"])

    assert result.exit_code == 0
    assert "--output" in result.stdout
    assert "--var" in result.stdout
    assert "--vars-file" in result.stdout
    assert "--non-interactive" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--overwrite" in result.stdout


def test_validate_with_valid_config_exits_zero(runner: CliRunner, tmp_path: Path) -> None:
    config_path = _write_valid_config(tmp_path)

    result = runner.invoke(app, ["validate", str(config_path)])

    assert result.exit_code == 0
    assert "Config is valid:" in result.output


def test_validate_with_invalid_config_exits_one_and_shows_all_issues(
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    config_path = _write_invalid_config(tmp_path)

    result = runner.invoke(app, ["validate", str(config_path)])

    assert result.exit_code == 1
    assert "sources[1].id" in result.output
    assert "variables.count.default" in result.output


def test_inspect_outputs_variable_and_source_tables(runner: CliRunner, tmp_path: Path) -> None:
    config_path = _write_valid_config(tmp_path, include_template=True)

    result = runner.invoke(app, ["inspect", str(config_path)])

    assert result.exit_code == 0
    assert "Variables" in result.output
    assert "project_name | str | demo | default" in result.output
    assert "Sources" in result.output
    assert f"base | local_dir | {tmp_path / 'template'}" in result.output
    assert "Merge Preview" in result.output
    assert str(tmp_path / "generated" / "README.md") in result.output


def test_error_formatting_produces_readable_output(runner: CliRunner, tmp_path: Path) -> None:
    config_path = E2E_DIR / "template" / "config.yml"
    output_path = tmp_path / "out"

    result = runner.invoke(
        app,
        ["generate", str(config_path), "--output", str(output_path), "--non-interactive"],
    )

    assert result.exit_code == 1
    assert "Error: VariableResolutionError" in result.output
    assert "Field: project_name" in result.output
    assert "Suggestion:" in result.output


def test_quiet_suppresses_info_level_output(runner: CliRunner, tmp_path: Path) -> None:
    config_path = _write_valid_config(tmp_path)

    result = runner.invoke(app, ["--quiet", "validate", str(config_path)])

    assert result.exit_code == 0
    assert result.output == ""


def test_system_errors_exit_with_code_two(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generate_module = importlib.import_module("mixy.cli.commands.generate")

    def fake_generate_project(*args: object, **kwargs: object) -> object:
        raise SourceResolutionError(
            "Git is not available on PATH. Install git to use git sources.",
            source_id="base",
            suggestion="Install git and retry.",
            system_error=True,
        )

    monkeypatch.setattr(generate_module, "generate_project", fake_generate_project)

    result = runner.invoke(app, ["generate", "mixy.yml"])

    assert result.exit_code == 2
    assert "Error: SourceResolutionError" in result.output
    assert "Source: base" in result.output


def test_unexpected_errors_show_generic_debug_hint(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generate_module = importlib.import_module("mixy.cli.commands.generate")

    def fake_generate_project(*args: object, **kwargs: object) -> object:
        raise RuntimeError("boom")

    monkeypatch.setattr(generate_module, "generate_project", fake_generate_project)

    result = runner.invoke(app, ["generate", "mixy.yml"])

    assert result.exit_code == 2
    assert "Error: UnexpectedError" in result.output
    assert "--log-level debug" in result.output


def _write_valid_config(tmp_path: Path, *, include_template: bool = False) -> Path:
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    if include_template:
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
    return config_path


def _write_invalid_config(tmp_path: Path) -> Path:
    template_dir = tmp_path / "template"
    template_dir.mkdir()

    config_path = tmp_path / "mixy-invalid.yml"
    config_path.write_text(
        'version: "1"\n'
        "variables:\n"
        "  count:\n"
        "    type: int\n"
        "    default: hello\n"
        "sources:\n"
        "  - id: base\n"
        "    source:\n"
        "      type: local_dir\n"
        f"      path: {template_dir}\n"
        "  - id: base\n"
        "    source:\n"
        "      type: local_dir\n"
        f"      path: {template_dir}\n",
        encoding="utf-8",
    )
    return config_path
