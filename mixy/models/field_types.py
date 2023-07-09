from pathlib import Path
from typing import TYPE_CHECKING

from pydantic.validators import path_validator

if TYPE_CHECKING:
    AbsolutePath = Path
else:

    class AbsolutePath(type(Path())):
        @classmethod
        def __get_validators__(cls):
            yield path_validator
            yield cls.validate

        @classmethod
        def validate(cls, v: Path) -> Path:
            if not v.is_absolute():
                raise ValueError(f"{v} is not an absolute path")
            return v
