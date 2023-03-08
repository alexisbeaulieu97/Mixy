from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SecretsResolver(Protocol):
    def secret(self, var_name: str) -> Any:
        ...
