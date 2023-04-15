from typing import Any

from mixy.protocols.basic_resolver import BasicResolver
from mixy.protocols.choices_resolver import ChoicesResolver
from mixy.protocols.secrets_resolver import SecretsResolver
from mixy.protocols.variable_resolver import VariableResolver

from .base import RenderableBaseModel


class ProjectVariables(RenderableBaseModel):
    standard: dict[str, Any] = {}
    secret: list[str] = []
    multi_choice: dict[str, list[Any]] = {}

    def resolve_basic(self, resolver: BasicResolver) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for k, v in self.standard.items():
            if isinstance(v, bool):
                resolved[k] = resolver.confirm(k, v)
            elif isinstance(v, list):
                resolved[k] = resolver.multi(k, v)  # type: ignore
            else:
                resolved[k] = resolver.regular(k, v)
        return resolved

    def resolve_secrets(self, resolver: SecretsResolver) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for secret in self.secret:
            resolved[secret] = resolver.secret(secret)
        return resolved

    def resolve_choices(self, resolver: ChoicesResolver) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for k, v in self.multi_choice.items():
            resolved[k] = resolver.choice(k, *v)
        return resolved

    def resolve(self, resolver: VariableResolver) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        resolved.update(self.resolve_basic(resolver))
        resolved.update(self.resolve_secrets(resolver))
        resolved.update(self.resolve_choices(resolver))
        return resolved
