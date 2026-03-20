"""Core enumerations for Mixy's domain layer."""

from enum import Enum


class ConflictPolicy(str, Enum):
    FAIL = "fail"
    OVERWRITE = "overwrite"
    SKIP = "skip"


class VariableType(str, Enum):
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"


class CopyMode(str, Enum):
    RENDER = "render"
    RAW = "raw"


class ConflictType(str, Enum):
    FILE_CONFLICT = "file_conflict"
    FILE_VS_DIRECTORY = "file_vs_directory"


class ValueSource(str, Enum):
    CLI = "cli"
    VARS_FILE = "vars-file"
    ENV = "env"
    CONFIG = "config"
    DEFAULT = "default"
    PROMPT = "prompt"
    UNRESOLVED = "unresolved"
