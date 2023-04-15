from typing import TypeVar

from pydantic import BaseModel, BaseSettings

from mixy.protocols.mergeable import Mergeable

T = TypeVar("T", BaseModel, BaseSettings)


class RecursiveMergeStrategy:
    def merge(self, a: T, b: T) -> None:
        for k, v in b.dict(exclude_unset=True).items():
            value = getattr(a, k)
            if isinstance(value, Mergeable):
                value.merge_with(v, self)
            else:
                setattr(a, k, v)
