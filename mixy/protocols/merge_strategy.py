from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel, BaseSettings

T = TypeVar("T", BaseModel, BaseSettings)


@runtime_checkable
class MergeStrategy(Protocol):
    def merge(self, a: T, b: T) -> None:
        ...
