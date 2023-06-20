from typing import Any, Iterable


class CacheHandler:
    def __init__(self):
        self._cache: dict[str, Any] = {}

    def clear_cache(self, keys: Iterable[str]) -> None:
        for key in keys:
            self._cache.pop(key, None)

    def add(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def get(self, key: str) -> Any:
        return self._cache.get(key)

    def contains(self, key: str) -> bool:
        return key in self._cache
