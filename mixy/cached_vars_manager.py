from __future__ import annotations

from typing import Any

from mixy.models.base import BaseModel
from mixy.models.template_var import TemplateVar
from mixy.plugins.plugin_manager import plugin_master


class CachedVarsManager(BaseModel):
    # TODO when we add vars, should we remove the values from the cache?
    vars: dict[str, TemplateVar] = {}
    _cache: dict[str, Any] = {}

    def add_vars(self, vars: dict[str, TemplateVar]) -> None:
        self.vars.update(vars)

    def add_values(self, values: dict[str, Any]) -> None:
        self._cache.update(values)

    def get_value(self, var_name: str) -> Any:
        if var_name in self._cache:
            return self._cache[var_name]
        else:
            config = self.vars[var_name]
            value = plugin_master.hook.resolve(
                var_name=var_name,
                var_config=config,
            )
            self._cache[var_name] = value
            return value

    def has_var(self, var_name: str) -> bool:
        return var_name in self.vars

    def get_vars_names(self) -> set[str]:
        return set(self.vars.keys())
