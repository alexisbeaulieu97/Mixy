from typing import Protocol, Self, runtime_checkable

from mixy.protocols.merge_strategy import MergeStrategy


@runtime_checkable
class Mergeable(Protocol):
    def merge_with(self, data: Self, strategy: MergeStrategy) -> None:
        ...
