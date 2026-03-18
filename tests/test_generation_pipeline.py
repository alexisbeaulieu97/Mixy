from pathlib import Path

import pytest

from mixy.application.use_cases.generate_project import generate_project
from mixy.domain.enums import ConflictPolicy
from mixy.domain.exceptions import ConfigValidationError, MergeConflictError
from mixy.domain.models import (
    CopyRaw,
    CreateDir,
    Overwrite,
    RenderedFile,
    RenderPlan,
    RenderTemplate,
    SkipExisting,
)
from mixy.infrastructure.filesystem import GenerationExecutor, GenerationResult

E2E_DIR = Path(__file__).parent / "fixtures" / "e2e"


def test_generate_from_local_source_end_to_end(
    tmp_path: Path,
) -> None:
    fixture = E2E_DIR / "template"
    result = generate_project(
        fixture / "config.yml",
        output_override=tmp_path / "out",
        var_overrides={"project_name": "mixy-demo"},
        non_interactive=True,
    )

    assert isinstance(result, GenerationResult)
    assert (tmp_path / "out" / "README.md").read_text() == "# mixy-demo\n"
    assert (tmp_path / "out" / "src" / "app.py").read_text() == (
        'def run():\n    return "mixy-demo"\n'
    )


def test_dry_run_produces_plan_without_creating_files(tmp_path: Path) -> None:
    fixture = E2E_DIR / "template"

    result = generate_project(
        fixture / "config.yml",
        output_override=tmp_path / "out",
        var_overrides={"project_name": "mixy-demo"},
        non_interactive=True,
        dry_run=True,
    )

    assert isinstance(result, str)
    assert "Action | Output Path | Source" in result
    assert not (tmp_path / "out").exists()


def test_pipeline_fails_before_writes_on_config_error(tmp_path: Path) -> None:
    broken_config = tmp_path / "broken.yml"
    broken_config.write_text(
        'version: "1"\n'
        "sources:\n"
        "  - id: base\n"
        "    source:\n"
        "      type: local_dir\n"
        "      path: ./one\n"
        "  - id: base\n"
        "    source:\n"
        "      type: local_dir\n"
        "      path: ./two\n",
        encoding="utf-8",
    )
    (tmp_path / "one").mkdir()
    (tmp_path / "two").mkdir()

    with pytest.raises(ConfigValidationError):
        generate_project(
            broken_config,
            output_override=tmp_path / "out",
            non_interactive=True,
        )

    assert not (tmp_path / "out").exists()


def test_pipeline_fails_before_writes_on_merge_conflict(tmp_path: Path) -> None:
    fixture = E2E_DIR / "conflict"

    with pytest.raises(MergeConflictError):
        generate_project(
            fixture / "config.yml",
            output_override=tmp_path / "out",
            non_interactive=True,
        )

    assert not (tmp_path / "out").exists()


def test_generation_executor_processes_each_operation_type(tmp_path: Path) -> None:
    executor = GenerationExecutor()
    output_root = tmp_path / "output"
    raw_source = tmp_path / "raw.txt"
    raw_source.write_text("raw", encoding="utf-8")
    rendered_source = tmp_path / "rendered.txt"
    rendered_source.write_text("rendered", encoding="utf-8")

    plan = RenderPlan(
        operations=[
            CreateDir(path=output_root),
            CopyRaw(
                source_path=raw_source,
                output_path=output_root / "raw.txt",
                source_id="base",
                rendered_file=RenderedFile(
                    output_name="raw.txt",
                    content=b"raw",
                    rendered=False,
                    is_binary=False,
                ),
            ),
            RenderTemplate(
                source_path=rendered_source,
                output_path=output_root / "rendered.txt",
                source_id="base",
                rendered_file=RenderedFile(
                    output_name="rendered.txt",
                    content=b"rendered",
                    rendered=True,
                    is_binary=False,
                ),
            ),
            Overwrite(
                source_path=rendered_source,
                output_path=output_root / "rendered.txt",
                source_id="override",
                previous_source_id="base",
                rendered_file=RenderedFile(
                    output_name="rendered.txt",
                    content=b"updated",
                    rendered=True,
                    is_binary=False,
                ),
            ),
            SkipExisting(
                source_path=rendered_source,
                output_path=output_root / "skipped.txt",
                source_id="skip",
                existing_source_id="base",
                reason="already exists",
            ),
        ],
        conflicts=[],
        conflict_policy=ConflictPolicy.OVERWRITE,
        output_path=output_root,
    )

    result = executor.execute(plan)

    assert (output_root / "raw.txt").read_text() == "raw"
    assert (output_root / "rendered.txt").read_text() == "updated"
    assert not (output_root / "skipped.txt").exists()
    assert result.created_count == 1
    assert result.copied_count == 1
    assert result.rendered_count == 2
    assert result.skipped_count == 1


def test_generation_result_counts_are_accurate() -> None:
    result = GenerationResult(
        output_path=Path("/tmp/out"),
        created_directories=[Path("/tmp/out")],
        rendered_files=[Path("/tmp/out/a"), Path("/tmp/out/b")],
        copied_files=[Path("/tmp/out/c")],
        skipped_files=[Path("/tmp/out/d")],
        failed_operations=[],
    )

    assert result.created_count == 1
    assert result.rendered_count == 2
    assert result.copied_count == 1
    assert result.skipped_count == 1
    assert result.failed_count == 0
    assert "Output: /tmp/out" in result.format_summary()
