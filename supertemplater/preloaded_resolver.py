from dataclasses import dataclass
from typing import Any, Optional, TypeVar


_T = TypeVar("_T")

@dataclass
class PreloadedResolver:
    variables: dict[str, Any]

    def _get(self, var_name: str, default: Optional[Any] = None) -> Any:
        if default is None:
            return self.variables[var_name]
        return self.variables.get(var_name, default)

    def regular(self, var_name: str, default: Any) -> str:
        return self._get(var_name, default)

    def multi(self, var_name: str, default: list[Any]) -> list[Any]:
        return self._get(var_name, default)

    def secret(self, var_name: str) -> str:
        return self._get(var_name)

    def confirm(self, var_name: str, default: bool) -> bool:
        return self._get(var_name, default)

    def choice(self, var_name: str, *_: _T) -> _T:
        return self._get(var_name)
