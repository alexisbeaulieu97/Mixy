import json
from enum import Enum
from functools import cached_property
from typing import Any, Self

from pydantic import BaseModel as BM

from supertemplater.context import Context
from supertemplater.protocols import Updatable


class BaseModel(BM):
    def update(self, data: Self) -> None:
        diff = data.dict(exclude_unset=True).keys()
        for k in diff:
            value = getattr(self, k)
            new_value = getattr(data, k)
            if isinstance(value, Updatable):
                value.update(new_value)
            else:
                setattr(self, k, new_value)

    class Config:
        underscore_attrs_are_private = True
        keep_untouched = (cached_property,)  # type: ignore
        validate_assignment = True


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
