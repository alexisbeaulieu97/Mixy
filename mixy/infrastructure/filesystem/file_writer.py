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
class GenerationResult:
    output_path: Path
    created_directories: list[Path] = field(default_factory=list)
    rendered_files: list[Path] = field(default_factory=list)
    copied_files: list[Path] = field(default_factory=list)
    skipped_files: list[Path] = field(default_factory=list)
    failed_operations: list[Path] = field(default_factory=list)

    @property
    def created_count(self) -> int:
        return len(self.created_directories)

    @property
    def rendered_count(self) -> int:
        return len(self.rendered_files)

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
        return self.created_count + self.rendered_count + self.copied_count + self.skipped_count

    def format_summary(self) -> str:
        return "\n".join(
            [
                "Generation Summary",
                f"Output: {self.output_path}",
                f"Directories created: {self.created_count}",
                f"Files rendered: {self.rendered_count}",
                f"Files copied: {self.copied_count}",
                f"Files skipped: {self.skipped_count}",
                f"Failures: {self.failed_count}",
            ]
        )


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
                    result.rendered_files.append(operation.output_path)
                elif isinstance(operation, SkipExisting):
                    result.skipped_files.append(operation.output_path)
            except OSError:
                target = (
                    operation.path if isinstance(operation, CreateDir) else operation.output_path
                )
                result.failed_operations.append(target)
                break

        return result

    def _write_bytes(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
