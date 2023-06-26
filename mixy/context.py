from copy import deepcopy
from dataclasses import dataclass, field
from typing import Self

from jinja2 import Environment, StrictUndefined

from mixy.cached_vars_manager import CachedVarsManager
from mixy.prompt_resolver import PromptResolver
from mixy.protocols.resolver_protocol import ResolverProtocol
from mixy.protocols.var_protocol import VarProtocol
from mixy.protocols.vars_manager_protocol import VarsManagerProtocol


@dataclass
class Context:
    env: Environment = field(default=Environment(undefined=StrictUndefined))
    resolver: ResolverProtocol = field(default_factory=PromptResolver)
    vars_manager: VarsManagerProtocol = field(default_factory=CachedVarsManager)

    def render(self, content: str) -> str:
        template = self.env.from_string(content)
        resolved_vars = self.vars_manager.resolve(self.resolver)
        return template.render(**resolved_vars)

    def update(self, **kwargs: dict[str, VarProtocol]) -> None:
        self.vars_manager.update(**kwargs)

    @classmethod
    def derive_from(cls, old_context: Self, **kwargs: dict[str, VarProtocol]) -> Self:
        new_context = cls(
            deepcopy(old_context.env),
            deepcopy(old_context.resolver),
            deepcopy(old_context.vars_manager),
        )
        new_context.update(**kwargs)
        return new_context
