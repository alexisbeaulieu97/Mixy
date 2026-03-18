"""Rendering infrastructure."""

from mixy.infrastructure.rendering.binary_detection import BINARY_EXTENSIONS, is_binary
from mixy.infrastructure.rendering.jinja_renderer import (
    has_jinja_suffix,
    render_string,
    strip_jinja_suffix,
)

__all__ = [
    "BINARY_EXTENSIONS",
    "has_jinja_suffix",
    "is_binary",
    "render_string",
    "strip_jinja_suffix",
]
