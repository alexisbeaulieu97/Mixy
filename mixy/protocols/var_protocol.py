from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class VarProtocol(Protocol):
    @property
    def description(self) -> str:
        ...

    @property
    def default(self) -> Any:
        ...

    @property
    def secret(self) -> bool:
        ...
