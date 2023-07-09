from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mixy.models.template_var import TemplateVar

import typer

from mixy.plugins.builtin import hook_impl


@hook_impl
def resolve(var_name: str, var_config: TemplateVar) -> Any | None:
    if var_config.resolver != "prompt":
        return
    return typer.prompt(
        typer.style(
            var_config.description or var_name,
            fg=typer.colors.BRIGHT_GREEN,
            bold=True,
        ),
        var_config.default,
    )
