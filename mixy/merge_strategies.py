from typing import TypeVar

from pydantic import BaseModel, BaseSettings

from mixy.protocols.mergeable import Mergeable

T = TypeVar("T", BaseModel, BaseSettings)


class RecursiveMergeStrategy:
    def merge(self, a: T, b: T) -> None:
        for k in b.dict(exclude_unset=True):
            value_a = getattr(a, k)
            value_b = getattr(b, k)
            if isinstance(value_a, Mergeable):
                value_a.merge_with(value_b, self)
            else:
                setattr(a, k, value_b)
