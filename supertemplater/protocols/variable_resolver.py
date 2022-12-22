from typing import Protocol

from .basic_resolver import BasicResolver
from .choices_resolver import ChoicesResolver
from .secrets_resolver import SecretsResolver


class VariableResolver(BasicResolver, SecretsResolver, ChoicesResolver, Protocol):
    ...
