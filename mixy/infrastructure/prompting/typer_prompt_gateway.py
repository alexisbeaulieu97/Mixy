"""Typer-backed prompt gateway."""

from __future__ import annotations

from typing import cast

import typer

from mixy.application.ports import PromptGateway


class TyperPromptGateway(PromptGateway):
    def prompt(self, text: str, *, hide_input: bool = False) -> str:
        return cast(str, typer.prompt(text, hide_input=hide_input))
