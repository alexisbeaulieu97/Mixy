from __future__ import annotations

from typing import Any

from pydantic import Field

from mixy.cache_manager import CacheManager
from mixy.models.base import BaseModel
from mixy.models.template_var import TemplateVar
from mixy.plugins.plugin_manager import plugin_master


class CachedVarsManager(BaseModel):
    vars: dict[str, TemplateVar] = Field({})
    _cache_manager: CacheManager = CacheManager()

    def add_vars(self, vars: dict[str, TemplateVar]) -> None:
        self._cache_manager.clear_cache(vars)
        self.vars.update(vars)

    def add_values(self, values: dict[str, Any]) -> None:
        for k, v in values.items():
            self._cache_manager.add(k, v)

    def get_value(self, var_name: str) -> Any:
        if self._cache_manager.contains(var_name):
            return self._cache_manager.get(var_name)
        else:
            config = self.vars[var_name]
            value = plugin_master.hook.resolve(
                var_name=var_name,
                var_config=config,
            )
            self._cache_manager.add(var_name, value)
            return value

    def has_var(self, var_name: str) -> bool:
        return var_name in self.vars

    def get_vars_names(self) -> set[str]:
        return set(self.vars.keys())
