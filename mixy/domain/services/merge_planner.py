"""Build deterministic merge plans from materialized sources."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

from mixy.domain.enums import ConflictPolicy
from mixy.domain.exceptions import MergeConflictError
from mixy.domain.models import (
    Conflict,
    CopyRaw,
    CreateDir,
    MaterializedSource,
    OutputDefinition,
    Overwrite,
    RenderedFile,
    RenderPlan,
    RenderTemplate,
    SkipExisting,
)
from mixy.domain.models.pre_merge_artifact import PreMergeArtifact, PreMergeEntry
from mixy.domain.services.metadata_resolver import is_metadata_path

RenderDecisionKey = tuple[str, str]


@dataclass(frozen=True, slots=True)
class PlannedEntry:
    source_id: str
    source_path: Path
    relative_path: Path
    output_path: Path
    rendered_file: RenderedFile


class MergePlanner:
    """Plan how ordered sources should be merged into one output tree."""

    def build_plan(
        self,
        sources: list[MaterializedSource],
        output: OutputDefinition,
        render_decisions: Mapping[RenderDecisionKey, RenderedFile],
        *,
        pre_merge_artifact: PreMergeArtifact | None = None,
    ) -> RenderPlan:
        artifact = pre_merge_artifact or self._collect_pre_merge_artifact(sources, render_decisions)
        directory_paths, file_entries = self._materialize_pre_merge_artifact(artifact, output.path)
        conflicts = self._detect_conflicts(directory_paths, file_entries)

        file_vs_directory = [
            conflict for conflict in conflicts if conflict.type == "file_vs_directory"
        ]
        if file_vs_directory:
            raise MergeConflictError(file_vs_directory)

        file_conflicts = [conflict for conflict in conflicts if conflict.type == "file_conflict"]
        if output.conflict_policy is ConflictPolicy.FAIL and file_conflicts:
            raise MergeConflictError(file_conflicts)

        operations: list[CreateDir | CopyRaw | Overwrite | RenderTemplate | SkipExisting] = [
            CreateDir(path=path)
            for path in sorted(
                directory_paths,
                key=lambda path: (len(path.parts), path.as_posix()),
            )
        ]
        operations.extend(self._build_file_operations(file_entries, output.conflict_policy))

        return RenderPlan(
            operations=operations,
            conflicts=conflicts,
            conflict_policy=output.conflict_policy,
            output_path=output.path,
        )

    def _collect_pre_merge_artifact(
        self,
        sources: list[MaterializedSource],
        render_decisions: Mapping[RenderDecisionKey, RenderedFile],
    ) -> PreMergeArtifact:
        directories: dict[Path, list[str]] = defaultdict(list)
        directories[Path(".")].append("<output>")
        entries: list[PreMergeEntry] = []

        for source in sources:
            for candidate in sorted(source.root_path.rglob("*")):
                relative = candidate.relative_to(source.root_path)
                if is_metadata_path(relative):
                    continue

                if candidate.is_dir():
                    directories[relative].append(source.source_id)
                elif candidate.is_file():
                    key = self.render_decision_key(source.source_id, relative)
                    decision = render_decisions[key]
                    entries.append(
                        PreMergeEntry(
                            source_id=source.source_id,
                            source_path=candidate,
                            relative_path=relative,
                            output_relative_path=(
                                decision.output_relative_path or relative.parent / decision.output_name
                            ),
                            rendered_file=decision,
                        )
                    )

        return PreMergeArtifact(
            directory_paths=dict(directories),
            file_entries=entries,
        )

    def _materialize_pre_merge_artifact(
        self,
        artifact: PreMergeArtifact,
        output_path: Path,
    ) -> tuple[dict[Path, list[str]], list[PlannedEntry]]:
        directories = {
            output_path if relative_path == Path(".") else output_path / relative_path: owner_ids
            for relative_path, owner_ids in artifact.directory_paths.items()
        }
        file_entries = [
            PlannedEntry(
                source_id=entry.source_id,
                source_path=entry.source_path,
                relative_path=entry.relative_path,
                output_path=output_path / entry.output_relative_path,
                rendered_file=entry.rendered_file,
            )
            for entry in artifact.file_entries
        ]
        return directories, file_entries

    def _detect_conflicts(
        self,
        directories: dict[Path, list[str]],
        file_entries: list[PlannedEntry],
    ) -> list[Conflict]:
        conflicts: list[Conflict] = []
        files_by_path: dict[Path, list[PlannedEntry]] = defaultdict(list)

        for entry in file_entries:
            files_by_path[entry.output_path].append(entry)

        for path, entries in files_by_path.items():
            if len(entries) < 2:
                continue
            for first, second in pairwise(entries):
                conflicts.append(
                    Conflict(
                        path=path,
                        source_a_id=first.source_id,
                        source_b_id=second.source_id,
                        type="file_conflict",
                    )
                )

        for directory, owner_ids in sorted(directories.items()):
            if directory not in files_by_path:
                continue
            for entry in files_by_path[directory]:
                directory_owner = owner_ids[-1]
                conflicts.append(
                    Conflict(
                        path=directory,
                        source_a_id=entry.source_id,
                        source_b_id=directory_owner,
                        type="file_vs_directory",
                    )
                )

        return conflicts

    def _build_file_operations(
        self,
        file_entries: list[PlannedEntry],
        conflict_policy: ConflictPolicy,
    ) -> list[CopyRaw | Overwrite | RenderTemplate | SkipExisting]:
        operations: list[CopyRaw | Overwrite | RenderTemplate | SkipExisting] = []
        chosen_by_output: dict[Path, PlannedEntry] = {}

        for entry in file_entries:
            current = chosen_by_output.get(entry.output_path)
            if current is None:
                chosen_by_output[entry.output_path] = entry
                operations.append(self._initial_operation(entry))
                continue

            if conflict_policy is ConflictPolicy.OVERWRITE:
                chosen_by_output[entry.output_path] = entry
                operations.append(
                    Overwrite(
                        source_path=entry.source_path,
                        output_path=entry.output_path,
                        source_id=entry.source_id,
                        previous_source_id=current.source_id,
                        rendered_file=entry.rendered_file,
                    )
                )
                continue

            operations.append(
                SkipExisting(
                    source_path=entry.source_path,
                    output_path=entry.output_path,
                    source_id=entry.source_id,
                    existing_source_id=current.source_id,
                    reason="Earlier source already mapped this output path.",
                )
            )

        return operations

    def _initial_operation(self, entry: PlannedEntry) -> CopyRaw | RenderTemplate:
        if entry.rendered_file.rendered:
            return RenderTemplate(
                source_path=entry.source_path,
                output_path=entry.output_path,
                source_id=entry.source_id,
                rendered_file=entry.rendered_file,
            )
        return CopyRaw(
            source_path=entry.source_path,
            output_path=entry.output_path,
            source_id=entry.source_id,
            rendered_file=entry.rendered_file,
        )

    @staticmethod
    def render_decision_key(source_id: str, relative_path: Path) -> RenderDecisionKey:
        return (source_id, relative_path.as_posix())
