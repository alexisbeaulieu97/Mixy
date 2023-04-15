from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel as BM
from pydantic import Extra

from mixy.context import Context
from mixy.merge_strategies import RecursiveMergeStrategy
from mixy.protocols.merge_strategy import MergeStrategy


class BaseModel(BM):
    def merge_with(
        self, data: Self, strategy: MergeStrategy = RecursiveMergeStrategy()
    ) -> None:
        strategy.merge(self, data)

    class Config:
        underscore_attrs_are_private = True
        keep_untouched = (cached_property,)  # type: ignore
        validate_assignment = True
        extra = Extra.forbid


class RenderableBaseModel(BaseModel):
    _RENDERABLE_EXCLUDES: set[str] = set()

    def _recursive_render(self, obj: Any, context: Context) -> Any:
        if isinstance(obj, str):
            return context.render(obj)
        elif isinstance(obj, Path):
            return Path(context.render(str(obj)))
        elif isinstance(obj, RenderableBaseModel):
            return obj.render(context)
        elif isinstance(obj, dict):
            return {k: self._recursive_render(v, context) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._recursive_render(x, context) for x in obj]
        elif hasattr(obj, "__dict__"):
            fields: dict[str, Any] = obj.__dict__
            for k, v in fields.items():
                if k.startswith("__"):
                    continue
                new_value = self._recursive_render(v, context)
                setattr(obj, k, new_value)
            return obj
        else:
            return obj

    def render(self, context: Context) -> Self:
        templated = self.dict(
            exclude={name: True for name in self._RENDERABLE_EXCLUDES}
        )
        not_templated = self.dict(
            include={name: True for name in self._RENDERABLE_EXCLUDES}
        )
        resolved_templated = self._recursive_render(templated, context)
        resolved: dict[str, Any] = {
            **resolved_templated,
            **not_templated,
        }
        return self.__class__(**resolved)


class NameBasedEnum(Enum):
    @classmethod
    def __get_validators__(cls):
        cls.name_lookup = {k: v for k, v in cls.__members__.items()}
        cls.value_lookup = {v.value: v for _, v in cls.__members__.items()}
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v
        if v in cls.value_lookup:
            return cls.value_lookup[v]
        if v in cls.name_lookup:
            return cls.name_lookup[v]

        raise ValueError(
            f'"{v}" is invalid, valid options are: {[k for k in cls.name_lookup]}'
        )
