"""CLI error and validation formatting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, NoReturn, cast

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


@dataclass(frozen=True)
class ErrorPresentation:
    exit_code: int
    message: str
    debug_exception: bool = False


Presenter = Callable[[Exception], ErrorPresentation]


def raise_cli_error(error: Exception) -> NoReturn:
    """Render an exception for CLI users and abort with the mapped exit code."""
    presentation = _presentation_for(error)

    if presentation.debug_exception:
        logger.opt(exception=error).debug("Unhandled exception while running Mixy.")

    typer.echo(presentation.message, err=True)
    raise typer.Exit(code=presentation.exit_code)


def get_exit_code(error: Exception) -> int:
    """Map a runtime error to the appropriate CLI exit code."""
    return _presentation_for(error).exit_code


def format_exception(error: Exception) -> str:
    """Return a user-facing error block for a CLI failure."""
    return _presentation_for(error).message


def format_validation_issue(issue: ValidationIssue) -> str:
    """Render a semantic validation issue."""
    parts = [issue.severity.upper(), issue.field_path, issue.message]
    if issue.suggestion:
        parts.append(f"Suggestion: {issue.suggestion}")
    return " | ".join(parts)


def _is_unexpected(error: Exception) -> bool:
    return not isinstance(error, (MixyError, ValueError, OSError))


def _presentation_for(error: Exception) -> ErrorPresentation:
    for error_type, renderer in _PRESENTERS:
        if isinstance(error, error_type):
            return renderer(error)

    return ErrorPresentation(
        exit_code=SYSTEM_ERROR_EXIT_CODE,
        message="\n".join(
            [
                "Error: UnexpectedError",
                "Message: Mixy hit an unexpected error.",
                "Suggestion: Re-run with `--log-level debug` to see the traceback.",
            ]
        ),
        debug_exception=True,
    )


def _lines(error: Exception) -> list[str]:
    return ["Error: %s" % error.__class__.__name__]


def _render_config_validation(error: ConfigValidationError) -> ErrorPresentation:
    lines = _lines(error)
    if error.field_path:
        lines.append("Field: %s" % error.field_path)
    lines.append("Message: %s" % error.args[0])
    lines.extend("Detail: %s" % detail for detail in error.details)
    if error.suggestion:
        lines.append("Suggestion: %s" % error.suggestion)
    return ErrorPresentation(USER_ERROR_EXIT_CODE, "\n".join(lines))


def _render_unsupported_version(error: UnsupportedVersionError) -> ErrorPresentation:
    return ErrorPresentation(
        USER_ERROR_EXIT_CODE,
        "\n".join(
            _lines(error)
            + [
                "Message: %s" % error,
                "Suggestion: Update the config version or use a Mixy version that supports it.",
            ]
        ),
    )


def _render_source_resolution(error: SourceResolutionError) -> ErrorPresentation:
    lines = _lines(error)
    if error.source_id:
        lines.append("Source: %s" % error.source_id)
    lines.append("Message: %s" % error)
    if error.suggestion:
        lines.append("Suggestion: %s" % error.suggestion)
    return ErrorPresentation(
        SYSTEM_ERROR_EXIT_CODE if error.system_error else USER_ERROR_EXIT_CODE,
        "\n".join(lines),
    )


def _render_variable_resolution(error: VariableResolutionError) -> ErrorPresentation:
    return ErrorPresentation(
        USER_ERROR_EXIT_CODE,
        "\n".join(
            _lines(error)
            + [
                "Field: %s" % error.variable_name,
                "Message: %s" % error.reason,
                "Suggestion: %s"
                % (
                    error.suggestion
                    or (
                        "Provide the value via `--var`, `--vars-file`, environment, "
                        "or config defaults."
                    )
                ),
            ]
        ),
    )


def _render_rendering(error: RenderingError) -> ErrorPresentation:
    lines = _lines(error) + [
        "Field: %s" % error.file_path,
        "Message: %s" % error.reason,
    ]
    if error.variable_name:
        lines.append("Variable: %s" % error.variable_name)
    lines.append(
        "Suggestion: %s"
        % (error.suggestion or "Ensure every referenced template variable resolves cleanly.")
    )
    return ErrorPresentation(USER_ERROR_EXIT_CODE, "\n".join(lines))


def _render_merge_conflict(error: MergeConflictError) -> ErrorPresentation:
    lines = _lines(error)
    lines.append("Message: %s" % error)
    lines.extend(
        "Detail: %s (%s vs %s)" % (conflict.path, conflict.source_a_id, conflict.source_b_id)
        for conflict in error.conflicts
    )
    lines.append(
        "Suggestion: %s"
        % (error.suggestion or "Retry with `--overwrite` or update the configured conflict policy.")
    )
    return ErrorPresentation(USER_ERROR_EXIT_CODE, "\n".join(lines))


def _render_file_not_found(error: FileNotFoundError) -> ErrorPresentation:
    return ErrorPresentation(
        USER_ERROR_EXIT_CODE,
        "\n".join(
            _lines(error)
            + [
                "Field: %s" % (Path(error.filename) if error.filename else "<path>"),
                "Message: %s" % (error.strerror or "File was not found."),
                "Suggestion: Check the path and try again.",
            ]
        ),
    )


def _render_os_error(error: OSError) -> ErrorPresentation:
    return ErrorPresentation(
        SYSTEM_ERROR_EXIT_CODE,
        "\n".join(
            _lines(error)
            + [
                "Message: %s" % (error.strerror or str(error)),
                "Suggestion: Check filesystem permissions and retry.",
            ]
        ),
    )


def _render_value_error(error: ValueError) -> ErrorPresentation:
    return ErrorPresentation(
        USER_ERROR_EXIT_CODE,
        "\n".join(_lines(error) + ["Message: %s" % error]),
    )


def _render_mixy_error(error: MixyError) -> ErrorPresentation:
    return ErrorPresentation(
        USER_ERROR_EXIT_CODE,
        "\n".join(_lines(error) + ["Message: %s" % error]),
    )


_PRESENTERS: list[tuple[type, Presenter]] = [
    (ConfigValidationError, cast(Presenter, _render_config_validation)),
    (UnsupportedVersionError, cast(Presenter, _render_unsupported_version)),
    (SourceResolutionError, cast(Presenter, _render_source_resolution)),
    (VariableResolutionError, cast(Presenter, _render_variable_resolution)),
    (RenderingError, cast(Presenter, _render_rendering)),
    (MergeConflictError, cast(Presenter, _render_merge_conflict)),
    (FileNotFoundError, cast(Presenter, _render_file_not_found)),
    (OSError, cast(Presenter, _render_os_error)),
    (ValueError, cast(Presenter, _render_value_error)),
    (MixyError, cast(Presenter, _render_mixy_error)),
]
