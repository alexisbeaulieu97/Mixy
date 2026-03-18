"""Application service for template rendering."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from jinja2 import TemplateError

from mixy.domain.exceptions import RenderingError
from mixy.domain.models import RenderedFile
from mixy.infrastructure.rendering.binary_detection import is_binary
from mixy.infrastructure.rendering.jinja_renderer import (
    UndefinedVariableError,
    has_jinja_suffix,
    render_string,
    strip_jinja_suffix,
)


class TemplateRenderer:
    """Render template paths and file contents using Jinja2."""

    def render_file(
        self,
        source_path: Path,
        context: Mapping[str, Any],
        render_policy: Mapping[str, Sequence[str]] | None = None,
        *,
        copy_mode: str | None = None,
        render_text_files: bool = True,
    ) -> RenderedFile:
        output_name = strip_jinja_suffix(source_path.name)
        forced_render = has_jinja_suffix(source_path.name)
        binary = is_binary(source_path)

        if binary:
            return RenderedFile(
                output_name=output_name,
                content=source_path.read_bytes(),
                rendered=False,
                is_binary=True,
            )

        should_render = forced_render or self.should_render(
            source_path,
            render_policy,
            copy_mode=copy_mode,
            render_text_files=render_text_files,
        )

        if not should_render:
            return RenderedFile(
                output_name=output_name,
                content=source_path.read_bytes(),
                rendered=False,
                is_binary=False,
            )

        try:
            rendered = render_string(source_path.read_text(encoding="utf-8"), dict(context))
        except UndefinedVariableError as error:
            raise RenderingError(
                file_path=str(source_path),
                variable_name=error.name,
                reason=str(error),
                suggestion="Provide the missing variable or update the template expression.",
            ) from error
        except TemplateError as error:
            raise RenderingError(
                file_path=str(source_path),
                variable_name=None,
                reason=str(error),
                suggestion="Provide the missing variable or update the template expression.",
            ) from error

        return RenderedFile(
            output_name=output_name,
            content=rendered.encode(),
            rendered=True,
            is_binary=False,
        )

    def render_path(self, name: str, context: Mapping[str, Any]) -> str:
        return self.render_path_segment(name, context, enabled=True)

    def render_path_segment(
        self,
        name: str,
        context: Mapping[str, Any],
        *,
        enabled: bool,
    ) -> str:
        if not enabled:
            return strip_jinja_suffix(name)

        try:
            rendered = render_string(name, dict(context))
        except UndefinedVariableError as error:
            raise RenderingError(
                file_path=name,
                variable_name=error.name,
                reason=str(error),
                suggestion="Ensure the rendered output path only uses defined variables.",
            ) from error
        except TemplateError as error:
            raise RenderingError(
                file_path=name,
                variable_name=None,
                reason=str(error),
                suggestion="Ensure the rendered output path only uses defined variables.",
            ) from error

        return strip_jinja_suffix(rendered)

    def is_excluded(
        self,
        source_path: Path,
        render_policy: Mapping[str, Sequence[str]] | None = None,
    ) -> bool:
        patterns = tuple(render_policy.get("exclude", ())) if render_policy else ()
        return any(
            fnmatch(source_path.name, pattern) or fnmatch(source_path.as_posix(), pattern)
            for pattern in patterns
        )

    def is_included(
        self,
        source_path: Path,
        render_policy: Mapping[str, Sequence[str]] | None = None,
    ) -> bool:
        patterns = tuple(render_policy.get("include", ())) if render_policy else ()
        if not patterns:
            return True

        return any(
            fnmatch(source_path.name, pattern) or fnmatch(source_path.as_posix(), pattern)
            for pattern in patterns
        )

    def should_render(
        self,
        source_path: Path,
        render_policy: Mapping[str, Sequence[str]] | None = None,
        *,
        copy_mode: str | None = None,
        render_text_files: bool = True,
    ) -> bool:
        if self.is_excluded(source_path, render_policy):
            return False
        if copy_mode == "raw":
            return False
        if not render_text_files:
            return self.is_included(source_path, render_policy)
        if copy_mode == "render":
            return True
        return self.is_included(source_path, render_policy)
