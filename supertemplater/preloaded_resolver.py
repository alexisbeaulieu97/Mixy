from dataclasses import dataclass
from typing import Any, Optional, TypeVar

from supertemplater.exceptions import InvalidChoiceError

_T = TypeVar("_T")


@dataclass
class PreloadedResolver:
    variables: dict[str, Any]

    def _get(self, var_name: str, default: Optional[Any] = None) -> Any:
        if default is None:
            return self.variables[var_name]
        return self.variables.get(var_name, default)

    def _assert_type(self, var_value: Any, var_name: str, var_type: type) -> None:
        if not isinstance(var_value, var_type):
            raise TypeError(
                f"Variable '{var_name}' must be of type '{var_type.__name__}'"
            )

    def regular(self, var_name: str, default: Any) -> str:
        return self._get(var_name, default)

    def multi(self, var_name: str, default: list[Any]) -> list[Any]:
        var_value = self._get(var_name, default)
        self._assert_type(var_value, var_name, list)
        return var_value

    def secret(self, var_name: str) -> str:
        return self._get(var_name)

    def confirm(self, var_name: str, default: bool) -> bool:
        var_value = self._get(var_name, default)
        self._assert_type(var_value, var_name, bool)
        return var_value

    def choice(self, var_name: str, *choices: _T) -> _T:
        c = self._get(var_name)
        if c not in choices:
            raise InvalidChoiceError(c, choices)
        return c
