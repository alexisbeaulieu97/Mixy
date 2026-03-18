"""Application-owned prompt contract."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PromptGateway(Protocol):
    def prompt(self, text: str, *, hide_input: bool = False) -> str:
        """Prompt the user for a value and return the entered text."""
