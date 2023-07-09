from __future__ import annotations

from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel as BM
from pydantic import Extra

from mixy.merge_strategies import RecursiveMergeStrategy

if TYPE_CHECKING:
    from mixy.protocols.merge_strategy import MergeStrategy


class BaseModel(BM):
    def merge_with(
        self, data: Self, strategy: MergeStrategy = RecursiveMergeStrategy()
    ) -> None:
        strategy.merge(self, data)

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True
        keep_untouched = (cached_property,)  # type: ignore
        validate_assignment = True
        extra = Extra.forbid


class NameBasedEnum(Enum):
    @classmethod
    def __get_validators__(cls):
        cls.name_lookup = {k: v for k, v in cls.__members__.items()}
        cls.value_lookup = {v.value: v for _, v in cls.__members__.items()}
        yield cls.validate

    @classmethod
    def validate(cls, v) -> Self:
        if isinstance(v, cls):
            return v
        if v in cls.value_lookup:
            return cls.value_lookup[v]
        if v in cls.name_lookup:
            return cls.name_lookup[v]

        raise ValueError(
            f'"{v}" is invalid, valid options are: {[k for k in cls.name_lookup]}'
        )
