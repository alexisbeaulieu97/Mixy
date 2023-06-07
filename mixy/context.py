from dataclasses import dataclass, field
from typing import Any

from jinja2 import Environment, StrictUndefined

from mixy.prompt_resolver import PromptResolver
from mixy.protocols.resolver import Resolver
from mixy.protocols.var_protocol import VarProtocol


@dataclass
class Context:
    env: Environment = Environment(undefined=StrictUndefined)
    resolver: Resolver = PromptResolver()
    _ctx: dict[str, VarProtocol] = field(default_factory=lambda: dict())
    _cache: dict[str, Any] = field(default_factory=lambda: dict())

    @property
    def variables(self) -> dict[str, VarProtocol]:
        return self._ctx

    @property
    def cache(self) -> dict[str, Any]:
        return self._cache

    def render(self, content: str) -> str:
        t = self.env.from_string(content)
        return t.render(self._resolve())

    def update(self, **kwargs: dict[str, VarProtocol]) -> None:
        self.variables.update(**kwargs)
        for k in kwargs:
            if k in self.cache:
                del self.cache[k]

    def _resolve(self) -> dict[str, Any]:
        variables = {}
        for var_name, var_config in self.variables.items():
            if var_name not in self.cache:
                self.cache[var_name] = self.resolver.resolve(var_name, var_config)
            variables[var_name] = self.cache[var_name]
        return variables
