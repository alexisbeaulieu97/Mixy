from typing import Any

from supertemplater.protocols import (
    BasicResolver,
    ChoicesResolver,
    SecretsResolver,
    VariableResolver,
)

from .base import RenderableBaseModel


class ProjectVariables(RenderableBaseModel):
    basic: dict[str, Any] = {}
    secrets: list[str] = []
    choices: dict[str, list[Any]] = {}

    def resolve_basic(self, resolver: BasicResolver) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for k, v in self.basic.items():
            if isinstance(v, bool):
                resolved[k] = resolver.confirm(k, v)
            elif isinstance(v, list):
                resolved[k] = resolver.multi(k, v)  # type: ignore
            else:
                resolved[k] = resolver.regular(k, v)
        return resolved

    def resolve_secrets(self, resolver: SecretsResolver) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for secret in self.secrets:
            resolved[secret] = resolver.secret(secret)
        return resolved

    def resolve_choices(self, resolver: ChoicesResolver) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for k, v in self.choices.items():
            resolved[k] = resolver.choice(k, *v)
        return resolved

    def resolve(self, resolver: VariableResolver) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        resolved.update(self.resolve_basic(resolver))
        resolved.update(self.resolve_secrets(resolver))
        resolved.update(self.resolve_choices(resolver))
        return resolved
