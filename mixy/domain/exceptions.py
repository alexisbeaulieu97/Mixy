"""Domain-specific exceptions for Mixy."""

from __future__ import annotations

from collections.abc import Sequence

from mixy.domain.models.conflict import Conflict


class MixyError(Exception):
    """Base exception for Mixy errors."""


class ConfigValidationError(MixyError):
    """Raised when a config file fails validation."""

    def __init__(
        self,
        message: str,
        *,
        field_path: str | None = None,
        suggestion: str | None = None,
        details: Sequence[str] | None = None,
    ) -> None:
        self.field_path = field_path
        self.suggestion = suggestion
        self.details = list(details or [])
        super().__init__(message)

    def __str__(self) -> str:
        message = super().__str__()
        if self.field_path:
            message = f"{self.field_path}: {message}"
        if self.suggestion:
            return f"{message} Suggestion: {self.suggestion}"
        return message


class UnsupportedVersionError(MixyError):
    """Raised when a config version is not supported."""

    def __init__(self, version: str, *, supported_version: str = "1") -> None:
        self.version = version
        self.supported_version = supported_version
        super().__init__(
            f'Unsupported config version "{version}". Supported version: "{supported_version}".'
        )


class SourceResolutionError(MixyError):
    """Raised when a source cannot be materialized."""

    def __init__(
        self,
        message: str,
        *,
        source_id: str | None = None,
        suggestion: str | None = None,
        system_error: bool = False,
    ) -> None:
        self.source_id = source_id
        self.suggestion = suggestion
        self.system_error = system_error
        super().__init__(message)


class VariableResolutionError(MixyError):
    """Raised when a variable cannot be resolved or validated."""

    def __init__(
        self,
        variable_name: str,
        value: object,
        reason: str,
        *,
        suggestion: str | None = None,
    ) -> None:
        self.variable_name = variable_name
        self.value = value
        self.reason = reason
        self.suggestion = suggestion
        super().__init__(
            f'Variable "{variable_name}" with value {value!r} failed resolution: {reason}'
        )


class RenderingError(MixyError):
    """Raised when template rendering fails."""

    def __init__(
        self,
        *,
        file_path: str,
        variable_name: str | None,
        reason: str,
        suggestion: str | None = None,
    ) -> None:
        self.file_path = file_path
        self.variable_name = variable_name
        self.reason = reason
        self.suggestion = suggestion
        super().__init__(f"{file_path}: {reason}")


class MergeConflictError(MixyError):
    """Raised when merge planning encounters conflicts."""

    def __init__(self, conflicts: Sequence[Conflict], *, suggestion: str | None = None) -> None:
        self.conflicts = list(conflicts)
        self.suggestion = suggestion
        super().__init__(f"Merge planning failed with {len(conflicts)} conflict(s).")


class MetadataValidationError(MixyError):
    """Raised when template metadata fails schema validation."""

    def __init__(
        self,
        message: str,
        *,
        file_path: str | None = None,
        field_path: str | None = None,
    ) -> None:
        self.file_path = file_path
        self.field_path = field_path
        super().__init__(message)

    def __str__(self) -> str:
        message = super().__str__()
        if self.field_path:
            message = f"{self.field_path}: {message}"
        if self.file_path:
            return f"{self.file_path}: {message}"
        return message


class MetadataConflictError(MixyError):
    """Raised when inherited template metadata contains incompatible refinements."""

    def __init__(
        self,
        message: str,
        *,
        variable_name: str | None = None,
        parent_scope: str | None = None,
        child_scope: str | None = None,
    ) -> None:
        self.variable_name = variable_name
        self.parent_scope = parent_scope
        self.child_scope = child_scope
        super().__init__(message)
