import importlib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mixy import get_version
from mixy.cli.app import app
from mixy.cli.errors import (
    SYSTEM_ERROR_EXIT_CODE,
    USER_ERROR_EXIT_CODE,
    format_exception,
    get_exit_code,
)
from mixy.domain.exceptions import ConfigValidationError, RenderingError, SourceResolutionError
from mixy.domain.models import MaterializedSource

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


def test_blocking_local_source_path_validation_is_consistent(
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    config_path = _write_missing_local_source_config(tmp_path)

    validate_result = runner.invoke(app, ["validate", str(config_path)])
    assert validate_result.exit_code == 1
    assert "ERROR | sources[0].source.path" in validate_result.output

    inspect_result = runner.invoke(app, ["inspect", str(config_path)])
    assert inspect_result.exit_code == 1
    assert "Error: ConfigValidationError" in inspect_result.output
    assert "Detail: sources[0].source.path: Local source path" in inspect_result.output

    generate_result = runner.invoke(app, ["generate", str(config_path), "--dry-run"])
    assert generate_result.exit_code == 1
    assert "Error: ConfigValidationError" in generate_result.output
    assert "Detail: sources[0].source.path: Local source path" in generate_result.output


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


def test_inspect_can_preview_without_output_path(runner: CliRunner, tmp_path: Path) -> None:
    config_path = _write_valid_config(tmp_path, include_template=True, include_output=False)

    result = runner.invoke(app, ["inspect", str(config_path)])

    assert result.exit_code == 0
    assert "Merge Preview" in result.output
    assert "<output>/README.md" in result.output


def test_generate_without_output_path_requires_override(
    runner: CliRunner,
    tmp_path: Path,
) -> None:
    config_path = _write_valid_config(tmp_path, include_template=True, include_output=False)

    result = runner.invoke(app, ["generate", str(config_path), "--dry-run"])

    assert result.exit_code == 1
    assert "Config must define an output path or provide an output override." in result.output


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


def test_cli_error_formatting_covers_validation_and_rendering_errors() -> None:
    validation_error = ConfigValidationError(
        "Config validation failed with 1 error(s).",
        field_path="sources[0].source.path",
        suggestion="Run `mixy validate config.yml` to inspect all validation issues.",
        details=["sources[0].source.path: Local source path does not exist."],
    )
    rendering_error = RenderingError(
        file_path="template.j2",
        variable_name="project_name",
        reason="Missing variable.",
        suggestion="Provide the missing variable or update the template expression.",
    )

    validation_output = format_exception(validation_error)
    assert "Error: ConfigValidationError" in validation_output
    assert "Field: sources[0].source.path" in validation_output
    assert (
        "Detail: sources[0].source.path: Local source path does not exist."
        in validation_output
    )
    assert (
        "Suggestion: Run `mixy validate config.yml` to inspect all validation issues."
        in validation_output
    )

    rendering_output = format_exception(rendering_error)
    assert "Error: RenderingError" in rendering_output
    assert "Field: template.j2" in rendering_output
    assert "Variable: project_name" in rendering_output
    assert "Message: Missing variable." in rendering_output


@pytest.mark.parametrize(
    ("error", "expected_exit_code"),
    [
        (
            ConfigValidationError("Config validation failed."),
            USER_ERROR_EXIT_CODE,
        ),
        (
            RenderingError(
                file_path="template.j2",
                variable_name=None,
                reason="Missing variable.",
            ),
            USER_ERROR_EXIT_CODE,
        ),
        (
            SourceResolutionError("Git is unavailable.", system_error=False),
            USER_ERROR_EXIT_CODE,
        ),
        (
            SourceResolutionError("Git is unavailable.", system_error=True),
            SYSTEM_ERROR_EXIT_CODE,
        ),
    ],
)
def test_get_exit_code_maps_representative_errors(
    error: Exception,
    expected_exit_code: int,
) -> None:
    assert get_exit_code(error) == expected_exit_code


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


def test_generate_and_inspect_share_source_provider_registry(
    runner: CliRunner,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_valid_config(tmp_path, include_template=True)
    template_dir = tmp_path / "template"

    class TrackingLocalProvider:
        def __init__(self) -> None:
            self.calls = 0

        def can_handle(self, source: object) -> bool:
            return getattr(source, "type", None) == "local_dir"

        def resolve(self, source: object) -> MaterializedSource:
            self.calls += 1
            return MaterializedSource(
                root_path=template_dir.resolve(),
                source_id="tracking",
                fingerprint="tracking",
            )

        def fingerprint(self, source: object) -> str:
            return "tracking"

    provider = TrackingLocalProvider()
    planning_module = importlib.import_module("mixy.application.use_cases.plan_project")
    monkeypatch.setattr(planning_module, "get_source_providers", lambda: [provider])

    inspect_result = runner.invoke(app, ["inspect", str(config_path)])
    assert inspect_result.exit_code == 0

    generate_result = runner.invoke(app, ["generate", str(config_path), "--dry-run"])
    assert generate_result.exit_code == 0
    assert "Action | Output Path | Source" in generate_result.output

    assert provider.calls == 2


def _write_valid_config(
    tmp_path: Path,
    *,
    include_template: bool = False,
    include_output: bool = True,
) -> Path:
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    if include_template:
        (template_dir / "README.md.j2").write_text("# {{ project_name }}\n", encoding="utf-8")

    config_lines = [
        'version: "1"',
        "variables:",
        "  project_name:",
        "    type: str",
        "    required: false",
        "    default: demo",
        "sources:",
        "  - id: base",
        "    source:",
        "      type: local_dir",
        f"      path: {template_dir}",
    ]
    if include_output:
        config_lines.extend(
            [
                "output:",
                f"  path: {tmp_path / 'generated'}",
            ]
        )

    config_path = tmp_path / "mixy.yml"
    config_path.write_text("\n".join(config_lines) + "\n", encoding="utf-8")
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


def _write_missing_local_source_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "mixy-missing-source.yml"
    config_path.write_text(
        'version: "1"\n'
        "sources:\n"
        "  - id: base\n"
        "    source:\n"
        "      type: local_dir\n"
        f"      path: {tmp_path / 'missing-template'}\n",
        encoding="utf-8",
    )
    return config_path
