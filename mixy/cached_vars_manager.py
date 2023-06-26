from dataclasses import dataclass, field
from typing import Any

from mixy.cache_manager import CacheManager
from mixy.protocols.resolver_protocol import ResolverProtocol
from mixy.protocols.var_protocol import VarProtocol


@dataclass
class CachedVarsManager:
    _vars: dict[str, VarProtocol] = field(default_factory=dict)
    _cache_manager: CacheManager = field(default_factory=CacheManager)

    def update(self, **kwargs: dict[str, VarProtocol]) -> None:
        self._vars.update(**kwargs)
        self._cache_manager.clear_cache(kwargs.keys())

    def resolve(self, resolver: ResolverProtocol) -> dict[str, Any]:
        variables = {}
        for var_name, var_config in self._vars.items():
            if not self._cache_manager.contains(var_name):
                self._cache_manager.add(
                    var_name, resolver.resolve(var_name, var_config)
                )
            variables[var_name] = self._cache_manager.get(var_name)
        return variables
