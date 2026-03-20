"""Jinja rendering helpers."""

from __future__ import annotations

from typing import Any

from jinja2 import Environment, StrictUndefined, UndefinedError

JINJA_SUFFIX = ".j2"


class UndefinedVariableError(UndefinedError):
    """Raised when a Jinja template references an undefined variable.

    Carries the variable name as a typed attribute.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__("'%s' is undefined" % name)


class TrackingStrictUndefined(StrictUndefined):
    def _fail_with_undefined_error(self, *args: Any, **kwargs: Any) -> Any:
        raise UndefinedVariableError(self._undefined_name or "unknown")


_ENVIRONMENT = Environment(undefined=TrackingStrictUndefined)


def render_string(template: str, context: dict[str, Any]) -> str:
    """Render text with strict undefined checking.

    Raises UndefinedVariableError with a stable `.name` attribute when a variable is missing.
    """
    try:
        return _ENVIRONMENT.from_string(template).render(context)
    except UndefinedVariableError:
        raise


def has_jinja_suffix(name: str) -> bool:
    return name.endswith(JINJA_SUFFIX)


def strip_jinja_suffix(name: str) -> str:
    if has_jinja_suffix(name):
        return name[: -len(JINJA_SUFFIX)]
    return name
