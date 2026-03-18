"""CLI error and validation formatting helpers."""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

import typer
from loguru import logger

from mixy.domain.exceptions import (
    ConfigValidationError,
    MergeConflictError,
    MixyError,
    RenderingError,
    SourceResolutionError,
    UnsupportedVersionError,
    VariableResolutionError,
)
from mixy.domain.services import ValidationIssue

SUCCESS_EXIT_CODE = 0
USER_ERROR_EXIT_CODE = 1
SYSTEM_ERROR_EXIT_CODE = 2


def raise_cli_error(error: Exception) -> NoReturn:
    """Render an exception for CLI users and abort with the mapped exit code."""
    exit_code = get_exit_code(error)

    if _is_unexpected(error):
        logger.opt(exception=error).debug("Unhandled exception while running Mixy.")

    typer.echo(format_exception(error), err=True)
    raise typer.Exit(code=exit_code)


def get_exit_code(error: Exception) -> int:
    """Map a runtime error to the appropriate CLI exit code."""
    if isinstance(error, (FileNotFoundError, ConfigValidationError)):
        return USER_ERROR_EXIT_CODE
    if isinstance(error, UnsupportedVersionError):
        return USER_ERROR_EXIT_CODE
    if isinstance(error, SourceResolutionError):
        return SYSTEM_ERROR_EXIT_CODE if error.system_error else USER_ERROR_EXIT_CODE
    if isinstance(error, (VariableResolutionError, RenderingError, MergeConflictError, ValueError)):
        return USER_ERROR_EXIT_CODE
    if isinstance(error, OSError):
        return SYSTEM_ERROR_EXIT_CODE
    if isinstance(error, MixyError):
        return USER_ERROR_EXIT_CODE
    return SYSTEM_ERROR_EXIT_CODE


def format_exception(error: Exception) -> str:
    """Return a user-facing error block for a CLI failure."""
    if _is_unexpected(error):
        return "\n".join(
            [
                "Error: UnexpectedError",
                "Message: Mixy hit an unexpected error.",
                "Suggestion: Re-run with `--log-level debug` to see the traceback.",
            ]
        )

    lines = [f"Error: {error.__class__.__name__}"]

    if isinstance(error, ConfigValidationError):
        if error.field_path:
            lines.append(f"Field: {error.field_path}")
        lines.append(f"Message: {error.args[0]}")
        lines.extend(f"Detail: {detail}" for detail in error.details)
        if error.suggestion:
            lines.append(f"Suggestion: {error.suggestion}")
        return "\n".join(lines)

    if isinstance(error, UnsupportedVersionError):
        lines.append(f"Message: {error}")
        lines.append(
            "Suggestion: Update the config version or use a Mixy version that supports it."
        )
        return "\n".join(lines)

    if isinstance(error, SourceResolutionError):
        if error.source_id:
            lines.append(f"Source: {error.source_id}")
        lines.append(f"Message: {error}")
        if error.suggestion:
            lines.append(f"Suggestion: {error.suggestion}")
        return "\n".join(lines)

    if isinstance(error, VariableResolutionError):
        lines.append(f"Field: {error.variable_name}")
        lines.append(f"Message: {error.reason}")
        lines.append(
            "Suggestion: "
            + (
                error.suggestion
                or "Provide the value via `--var`, `--vars-file`, environment, or config defaults."
            )
        )
        return "\n".join(lines)

    if isinstance(error, RenderingError):
        lines.append(f"Field: {error.file_path}")
        lines.append(f"Message: {error.reason}")
        if error.variable_name:
            lines.append(f"Variable: {error.variable_name}")
        lines.append(
            "Suggestion: "
            + (error.suggestion or "Ensure every referenced template variable resolves cleanly.")
        )
        return "\n".join(lines)

    if isinstance(error, MergeConflictError):
        lines.append(f"Message: {error}")
        lines.extend(
            f"Detail: {conflict.path} ({conflict.source_a_id} vs {conflict.source_b_id})"
            for conflict in error.conflicts
        )
        lines.append(
            "Suggestion: "
            + (
                error.suggestion
                or "Retry with `--overwrite` or update the configured conflict policy."
            )
        )
        return "\n".join(lines)

    if isinstance(error, FileNotFoundError):
        lines.append(f"Field: {Path(error.filename) if error.filename else '<path>'}")
        lines.append(f"Message: {error.strerror or 'File was not found.'}")
        lines.append("Suggestion: Check the path and try again.")
        return "\n".join(lines)

    if isinstance(error, OSError):
        lines.append(f"Message: {error.strerror or str(error)}")
        lines.append("Suggestion: Check filesystem permissions and retry.")
        return "\n".join(lines)

    if isinstance(error, ValueError):
        lines.append(f"Message: {error}")
        return "\n".join(lines)

    lines.append(f"Message: {error}")
    return "\n".join(lines)


def format_validation_issue(issue: ValidationIssue) -> str:
    """Render a semantic validation issue."""
    parts = [issue.severity.upper(), issue.field_path, issue.message]
    if issue.suggestion:
        parts.append(f"Suggestion: {issue.suggestion}")
    return " | ".join(parts)


def _is_unexpected(error: Exception) -> bool:
    return not isinstance(error, (MixyError, ValueError, OSError))
