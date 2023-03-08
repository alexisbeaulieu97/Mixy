from typing import Protocol, runtime_checkable

from supertemplater.context import Context


@runtime_checkable
class Renderable(Protocol):
    def render(self, ctx: Context) -> None:
        ...
