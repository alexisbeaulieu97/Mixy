"""Filesystem execution for render plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mixy.domain.models import (
    CopyRaw,
    CreateDir,
    Overwrite,
    RenderPlan,
    RenderTemplate,
    SkipExisting,
)


@dataclass(frozen=True, slots=True)
class GenerationFailure:
    operation: str
    target_path: Path
    reason: str
    source_path: Path | None = None
    source_id: str | None = None
    previous_source_id: str | None = None


@dataclass(frozen=True, slots=True)
class GenerationResult:
    output_path: Path
    created_directories: list[Path] = field(default_factory=list)
    rendered_files: list[Path] = field(default_factory=list)
    overwritten_files: list[Path] = field(default_factory=list)
    copied_files: list[Path] = field(default_factory=list)
    skipped_files: list[Path] = field(default_factory=list)
    failed_operations: list[Path] = field(default_factory=list)
    failed_operation_details: list[GenerationFailure] = field(default_factory=list)

    @property
    def created_count(self) -> int:
        return len(self.created_directories)

    @property
    def rendered_count(self) -> int:
        return len(self.rendered_files)

    @property
    def overwritten_count(self) -> int:
        return len(self.overwritten_files)

    @property
    def copied_count(self) -> int:
        return len(self.copied_files)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_files)

    @property
    def failed_count(self) -> int:
        return len(self.failed_operations)

    @property
    def success_count(self) -> int:
        return (
            self.created_count
            + self.rendered_count
            + self.overwritten_count
            + self.copied_count
            + self.skipped_count
        )

    def format_summary(self) -> str:
        status = "Partial failure" if self.failed_count else "Complete"
        return "\n".join(
            [
                "Generation Summary",
                f"Output: {self.output_path}",
                f"Status: {status}",
                f"Directories created: {self.created_count}",
                f"Files rendered: {self.rendered_count}",
                f"Files overwritten: {self.overwritten_count}",
                f"Files copied: {self.copied_count}",
                f"Files skipped: {self.skipped_count}",
                f"Failures: {self.failed_count}",
                *self._format_failure_lines(),
            ]
        )

    def _format_failure_lines(self) -> list[str]:
        if not self.failed_operation_details:
            return []

        failure = self.failed_operation_details[0]
        lines = [f"Failure: {failure.operation} | {failure.target_path}"]
        if failure.source_id:
            lines.append(f"Source: {failure.source_id}")
        if failure.source_path is not None:
            lines.append(f"Source Path: {failure.source_path}")
        if failure.previous_source_id:
            lines.append(f"Previous Source: {failure.previous_source_id}")
        lines.append(f"Reason: {failure.reason}")
        return lines


class GenerationExecutor:
    """Apply a render plan to the filesystem."""

    def execute(self, plan: RenderPlan) -> GenerationResult:
        result = GenerationResult(output_path=plan.output_path)

        for operation in plan.operations:
            try:
                if isinstance(operation, CreateDir):
                    operation.path.mkdir(parents=True, exist_ok=True)
                    result.created_directories.append(operation.path)
                elif isinstance(operation, CopyRaw):
                    self._write_bytes(operation.output_path, operation.rendered_file.content)
                    result.copied_files.append(operation.output_path)
                elif isinstance(operation, RenderTemplate):
                    self._write_bytes(operation.output_path, operation.rendered_file.content)
                    result.rendered_files.append(operation.output_path)
                elif isinstance(operation, Overwrite):
                    self._write_bytes(operation.output_path, operation.rendered_file.content)
                    result.overwritten_files.append(operation.output_path)
                elif isinstance(operation, SkipExisting):
                    result.skipped_files.append(operation.output_path)
            except OSError as error:
                target = (
                    operation.path if isinstance(operation, CreateDir) else operation.output_path
                )
                result.failed_operations.append(target)
                result.failed_operation_details.append(
                    GenerationFailure(
                        operation=operation.__class__.__name__,
                        target_path=target,
                        reason=str(error),
                        source_path=getattr(operation, "source_path", None),
                        source_id=getattr(operation, "source_id", None),
                        previous_source_id=getattr(operation, "previous_source_id", None),
                    )
                )
                break

        return result

    def _write_bytes(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
