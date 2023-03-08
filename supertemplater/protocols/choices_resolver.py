from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ChoicesResolver(Protocol):
    def choice(self, var_name: str, *options: list[Any]) -> Any:
        ...
