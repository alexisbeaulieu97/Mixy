from dataclasses import dataclass, field
from typing import Any
from copy import deepcopy

from jinja2 import Environment, StrictUndefined


@dataclass
class Context:
    env: Environment = Environment(undefined=StrictUndefined)
    _ctx: dict[str, Any] = field(default_factory=lambda: dict())

    @property
    def variables(self) -> dict[str, Any]:
        return deepcopy(self._ctx)

    def render(self, content: str) -> str:
        t = self.env.from_string(content)
        return t.render(self._ctx)

    def update(self, **kwargs: dict[str, Any]) -> None:
        self._ctx.update(**kwargs)
