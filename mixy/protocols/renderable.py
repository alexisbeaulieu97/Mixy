from typing import Protocol, runtime_checkable

from mixy.context import Context


@runtime_checkable
class Renderable(Protocol):
    def render(self, ctx: Context) -> None:
        ...
