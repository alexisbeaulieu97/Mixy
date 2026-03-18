"""Jinja rendering helpers."""

from __future__ import annotations

import re
from typing import Any

from jinja2 import Environment, StrictUndefined, UndefinedError

JINJA_SUFFIX = ".j2"

_ENVIRONMENT = Environment(undefined=StrictUndefined)

_UNDEFINED_VAR_RE = re.compile(r"'([^']+)' is undefined")


class UndefinedVariableError(UndefinedError):
    """Raised when a Jinja template references an undefined variable.

    Carries the variable name as a typed attribute. Subclasses UndefinedError
    so existing callers that catch UndefinedError continue to work.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"'{name}' is undefined")


def render_string(template: str, context: dict[str, Any]) -> str:
    """Render text with strict undefined checking.

    Raises UndefinedVariableError (with .name) when a variable is missing,
    rather than jinja2's generic UndefinedError.
    """
    try:
        return _ENVIRONMENT.from_string(template).render(context)
    except UndefinedError as error:
        match = _UNDEFINED_VAR_RE.search(str(error))
        name = match.group(1) if match else str(error)
        raise UndefinedVariableError(name) from error


def has_jinja_suffix(name: str) -> bool:
    return name.endswith(JINJA_SUFFIX)


def strip_jinja_suffix(name: str) -> str:
    if has_jinja_suffix(name):
        return name[: -len(JINJA_SUFFIX)]
    return name
