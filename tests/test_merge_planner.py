from pathlib import Path

import pytest

from mixy.domain.enums import ConflictPolicy, ConflictType
from mixy.domain.exceptions import MergeConflictError
from mixy.domain.models import (
    CopyRaw,
    CreateDir,
    MaterializedSource,
    OutputDefinition,
    Overwrite,
    RenderedFile,
    RenderTemplate,
    SkipExisting,
)
from mixy.domain.models.pre_merge_artifact import PreMergeArtifact, PreMergeEntry
from mixy.domain.services import MergePlanner
from mixy.domain.services.metadata_resolver import is_metadata_path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "merge"


def test_single_source_no_conflicts_creates_operations() -> None:
    planner = MergePlanner()
    source = materialized("source-a")

    plan = planner.build_plan([source], output_definition(), render_decisions_for([source]))

    assert any(isinstance(operation, CreateDir) for operation in plan.operations)
    file_operations = [op for op in plan.operations if isinstance(op, (CopyRaw, RenderTemplate))]
    assert len(file_operations) == 3
    assert [op.output_path.name for op in file_operations] == [
        "README.md",
        "only-a.txt",
        "utils.py",
    ]


def test_two_sources_without_conflicts_merge_in_source_order() -> None:
    planner = MergePlanner()
    sources = [materialized("source-a"), materialized("source-c")]

    plan = planner.build_plan(sources, output_definition(), render_decisions_for(sources))

    file_operations = [op for op in plan.operations if isinstance(op, (CopyRaw, RenderTemplate))]
    assert [op.source_id for op in file_operations] == [
        "source-a",
        "source-a",
        "source-a",
        "source-c",
    ]


def test_fail_policy_raises_with_all_file_conflicts() -> None:
    planner = MergePlanner()
    sources = [materialized("source-a"), materialized("source-b")]

    with pytest.raises(MergeConflictError) as error:
        planner.build_plan(
            sources,
            output_definition(ConflictPolicy.FAIL),
            render_decisions_for(sources),
        )

    conflicts = error.value.conflicts
    assert len(conflicts) == 1
    assert conflicts[0].path.name == "README.md"


def test_overwrite_policy_uses_later_source() -> None:
    planner = MergePlanner()
    sources = [materialized("source-a"), materialized("source-b")]

    plan = planner.build_plan(
        sources,
        output_definition(ConflictPolicy.OVERWRITE),
        render_decisions_for(sources),
    )

    overwrite_ops = [op for op in plan.operations if isinstance(op, Overwrite)]
    assert len(overwrite_ops) == 1
    assert overwrite_ops[0].source_id == "source-b"
    assert overwrite_ops[0].previous_source_id == "source-a"


def test_skip_policy_keeps_earlier_source() -> None:
    planner = MergePlanner()
    sources = [materialized("source-a"), materialized("source-b")]

    plan = planner.build_plan(
        sources,
        output_definition(ConflictPolicy.SKIP),
        render_decisions_for(sources),
    )

    skip_ops = [op for op in plan.operations if isinstance(op, SkipExisting)]
    assert len(skip_ops) == 1
    assert skip_ops[0].source_id == "source-b"
    assert skip_ops[0].existing_source_id == "source-a"


def test_file_vs_directory_conflict_always_fails() -> None:
    planner = MergePlanner()
    sources = [materialized("file-dir-a"), materialized("file-dir-b")]

    with pytest.raises(MergeConflictError) as error:
        planner.build_plan(
            sources,
            output_definition(ConflictPolicy.OVERWRITE),
            render_decisions_for(sources),
        )

    assert error.value.conflicts[0].type is ConflictType.FILE_VS_DIRECTORY


def test_recursive_directory_merging_creates_shared_directory_once() -> None:
    planner = MergePlanner()
    sources = [materialized("source-a"), materialized("source-b")]

    plan = planner.build_plan(
        sources,
        output_definition(ConflictPolicy.OVERWRITE),
        render_decisions_for(sources),
    )

    src_dirs = [
        operation.path
        for operation in plan.operations
        if isinstance(operation, CreateDir) and operation.path.name == "src"
    ]
    assert len(src_dirs) == 1


def test_metadata_files_are_excluded_from_plans() -> None:
    planner = MergePlanner()
    source = materialized("../metadata/recursive")

    plan = planner.build_plan([source], output_definition(), render_decisions_for([source]))

    output_paths = {str(path) for path in plan.list_output_paths()}
    assert not any(".mixy" in path for path in output_paths)
    assert not any(path.endswith(".mixy.yml") for path in output_paths)


def test_pre_merge_artifact_path_matches_direct_collection() -> None:
    planner = MergePlanner()
    sources = [materialized("source-a"), materialized("source-b")]
    render_decisions = render_decisions_for(sources)
    expected = planner.build_plan(
        sources,
        output_definition(ConflictPolicy.OVERWRITE),
        render_decisions,
    )

    actual = planner.build_plan(
        sources,
        output_definition(ConflictPolicy.OVERWRITE),
        render_decisions,
        pre_merge_artifact=pre_merge_artifact_for(sources, render_decisions),
    )

    assert [
        (type(op), getattr(op, "output_path", getattr(op, "path", None)))
        for op in actual.operations
    ] == [
        (type(op), getattr(op, "output_path", getattr(op, "path", None)))
        for op in expected.operations
    ]
    assert actual.conflicts == expected.conflicts


def test_pre_merge_artifact_preserves_empty_directories(tmp_path: Path) -> None:
    planner = MergePlanner()
    source_root = tmp_path / "source"
    (source_root / "empty").mkdir(parents=True)
    (source_root / "README.md").write_text("hello\n", encoding="utf-8")
    source = MaterializedSource(root_path=source_root, source_id="source", fingerprint="source")
    render_decisions = render_decisions_for([source])

    plan = planner.build_plan(
        [source],
        output_definition(),
        render_decisions,
        pre_merge_artifact=pre_merge_artifact_for([source], render_decisions),
    )

    created_dirs = {
        operation.path for operation in plan.operations if isinstance(operation, CreateDir)
    }
    assert output_definition().path / "empty" in created_dirs


def test_render_plan_lists_all_output_paths() -> None:
    planner = MergePlanner()
    source = materialized("source-a")

    plan = planner.build_plan([source], output_definition(), render_decisions_for([source]))

    listed = plan.list_output_paths()
    assert output_definition().path in listed
    assert output_definition().path / "README.md" in listed
    assert output_definition().path / "src" / "utils.py" in listed


def materialized(name: str) -> MaterializedSource:
    root = FIXTURES_DIR / name
    return MaterializedSource(
        root_path=root,
        source_id=name,
        fingerprint=name,
    )


def output_definition(
    conflict_policy: ConflictPolicy = ConflictPolicy.FAIL,
) -> OutputDefinition:
    return OutputDefinition(path=Path("/tmp/output"), conflict_policy=conflict_policy)


def render_decisions_for(
    sources: list[MaterializedSource],
) -> dict[tuple[str, str], RenderedFile]:
    planner = MergePlanner()
    decisions: dict[tuple[str, str], RenderedFile] = {}

    for source in sources:
        for file_path in sorted(path for path in source.root_path.rglob("*") if path.is_file()):
            relative = file_path.relative_to(source.root_path)
            decisions[planner.render_decision_key(source.source_id, relative)] = RenderedFile(
                output_name=file_path.name,
                content=file_path.read_bytes(),
                rendered=file_path.suffix in {".md", ".py", ".txt"},
                is_binary=False,
            )

    return decisions


def pre_merge_artifact_for(
    sources: list[MaterializedSource],
    render_decisions: dict[tuple[str, str], RenderedFile],
) -> PreMergeArtifact:
    planner = MergePlanner()
    directory_paths: dict[Path, list[str]] = {Path("."): ["<output>"]}
    file_entries: list[PreMergeEntry] = []

    for source in sources:
        for candidate in sorted(source.root_path.rglob("*")):
            relative = candidate.relative_to(source.root_path)
            if is_metadata_path(relative):
                continue
            if candidate.is_dir():
                directory_paths.setdefault(relative, []).append(source.source_id)
                continue

            key = planner.render_decision_key(source.source_id, relative)
            decision = render_decisions[key]
            file_entries.append(
                PreMergeEntry(
                    source_id=source.source_id,
                    source_path=candidate,
                    relative_path=relative,
                    output_relative_path=decision.output_relative_path
                    or relative.parent / decision.output_name,
                    rendered_file=decision,
                )
            )

    return PreMergeArtifact(directory_paths=directory_paths, file_entries=file_entries)
