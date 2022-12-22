from typing import Any, Protocol


class SecretsResolver(Protocol):
    def secret(self, var_name: str) -> Any:
        ...
