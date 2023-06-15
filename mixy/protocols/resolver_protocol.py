from typing import Any, Protocol, runtime_checkable

from mixy.protocols.var_protocol import VarProtocol


@runtime_checkable
class ResolverProtocol(Protocol):
    def resolve(self, var_name: str, var_config: VarProtocol) -> Any:
        ...
