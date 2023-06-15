from typing import Any, Protocol, runtime_checkable

from .resolver_protocol import ResolverProtocol
from .var_protocol import VarProtocol


@runtime_checkable
class VarsHandlerProtocol(Protocol):
    def update(self, **kwargs: dict[str, VarProtocol]) -> None:
        ...

    def resolve(self, resolver: ResolverProtocol) -> dict[str, Any]:
        ...
