from typing import TypeVar

from pydantic import BaseModel, BaseSettings

from supertemplater.protocols.mergeable import Mergeable

T = TypeVar("T", BaseModel, BaseSettings)


class RecursiveMergeStrategy:
    def merge(self, a: T, b: T) -> None:
        diff = b.dict(exclude_unset=True).keys()
        for k in diff:
            value = getattr(a, k)
            new_value = getattr(a, k)
            if isinstance(value, Mergeable):
                value.merge_with(new_value, self)
            else:
                setattr(a, k, new_value)
