from copy import deepcopy
from dataclasses import dataclass, field
from typing import Self

from jinja2 import Environment, StrictUndefined

from mixy.cached_vars_handler import CachedVarsHandler
from mixy.prompt_resolver import PromptResolver
from mixy.protocols.resolver_protocol import ResolverProtocol
from mixy.protocols.var_protocol import VarProtocol
from mixy.protocols.vars_handler_protocol import VarsHandlerProtocol


@dataclass
class Context:
    env: Environment = Environment(undefined=StrictUndefined)
    resolver: ResolverProtocol = field(default_factory=PromptResolver)
    vars_handler: VarsHandlerProtocol = field(default_factory=CachedVarsHandler)

    def render(self, content: str) -> str:
        template = self.env.from_string(content)
        return template.render(self.vars_handler.resolve(self.resolver))

    def update(self, **kwargs: dict[str, VarProtocol]) -> None:
        self.vars_handler.update(**kwargs)

    @classmethod
    def derive_from(cls, old_context: Self, **kwargs: dict[str, VarProtocol]) -> Self:
        new_context = cls(
            deepcopy(old_context.env),
            deepcopy(old_context.resolver),
            deepcopy(old_context.vars_handler),
        )
        new_context.update(**kwargs)
        return new_context
