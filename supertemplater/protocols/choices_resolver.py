from typing import Any, Protocol


class ChoicesResolver(Protocol):
    def choice(self, var_name: str, *options: list[Any]) -> Any:
        ...
