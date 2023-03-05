from typing import Protocol

from supertemplater.context import Context


class Renderable(Protocol):
    def render(self, ctx: Context) -> None:
        ...
