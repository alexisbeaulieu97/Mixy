"""Jinja rendering helpers."""

from __future__ import annotations

from typing import Any

from jinja2 import Environment, StrictUndefined

JINJA_SUFFIX = ".j2"

_ENVIRONMENT = Environment(undefined=StrictUndefined)


def render_string(template: str, context: dict[str, Any]) -> str:
    """Render text with Jinja2 StrictUndefined."""
    return _ENVIRONMENT.from_string(template).render(context)


def has_jinja_suffix(name: str) -> bool:
    return name.endswith(JINJA_SUFFIX)


def strip_jinja_suffix(name: str) -> str:
    if has_jinja_suffix(name):
        return name[: -len(JINJA_SUFFIX)]
    return name
