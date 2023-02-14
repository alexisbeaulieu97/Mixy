import json
from enum import Enum
from functools import cached_property
from typing import Any, Self

from pydantic import BaseModel as BM

from supertemplater.context import Context


class BaseModel(BM):
    class Config:
        underscore_attrs_are_private = True
        keep_untouched = (cached_property,)  # type: ignore


class RenderableBaseModel(BaseModel):
    _RENDERABLE_EXCLUDES: set[str] = set()

    def render(self, context: Context) -> Self:
        # TODO make this recursive
        templated = self.json(
            exclude={name: True for name in self._RENDERABLE_EXCLUDES}
        )
        not_templated = self.json(
            include={name: True for name in self._RENDERABLE_EXCLUDES}
        )
        resolved_templated = context.render(templated)
        resolved: dict[str, Any] = {
            **json.loads(resolved_templated),
            **json.loads(not_templated),
        }
        return self.__class__(**resolved)


class NameBasedEnum(Enum):
    @classmethod
    def __get_validators__(cls):
        cls.name_lookup = {v: k.value for v, k in cls.__members__.items()}
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            if v in cls.name_lookup.values():
                return v
            return cls.name_lookup[v]
        except KeyError:
            raise ValueError(
                f'"{v}" is invalid, valid options are: {[k for k in cls.name_lookup]}'
            )
