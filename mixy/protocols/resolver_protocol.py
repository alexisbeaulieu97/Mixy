from typing import Any, Protocol, runtime_checkable

from mixy.models.template_var import TemplateVar


@runtime_checkable
class ResolverProtocol(Protocol):
    def resolve(self, var_name: str, var_config: TemplateVar) -> Any:
        ...
