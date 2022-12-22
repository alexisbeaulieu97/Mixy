from typing import Any, Protocol


class BasicResolver(Protocol):
    def regular(self, var_name: str, default: Any) -> Any:
        ...

    def confirm(self, var_name: str, default: bool) -> bool:
        ...

    def multi(self, var_name: str, default: list[Any]) -> list[Any]:
        ...
