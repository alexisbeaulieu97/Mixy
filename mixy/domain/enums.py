"""Core enumerations for Mixy's domain layer."""

from enum import StrEnum


class ConflictPolicy(StrEnum):
    FAIL = "fail"
    OVERWRITE = "overwrite"
    SKIP = "skip"


class VariableType(StrEnum):
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
