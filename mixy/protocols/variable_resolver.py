from typing import Protocol, runtime_checkable

from .basic_resolver import BasicResolver
from .choices_resolver import ChoicesResolver
from .secrets_resolver import SecretsResolver


@runtime_checkable
class VariableResolver(BasicResolver, SecretsResolver, ChoicesResolver, Protocol):
    ...
