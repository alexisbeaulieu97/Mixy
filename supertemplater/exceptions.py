from pathlib import Path
from typing import Iterable, TypeVar

T = TypeVar("T")


class MissingProjectConfigurationError(Exception):
    """Raised when the project configuration file does not exist."""

    def __init__(self, config_file: Path) -> None:
        super().__init__(
            f'The project configuration file "{config_file}" is not a file or does not exist.'
        )


class ProjectAlreadyExistsError(Exception):
    """Raised then attempting to create a project which already exists."""

    def __init__(self, project_dest: Path) -> None:
        super().__init__(
            f'The project already exists. Please empty "{project_dest}" or use the --force option.'
        )


class InvalidChoiceError(Exception):
    """Raised when an the provided choice is not part of the choices."""

    def __init__(self, choice: T, choices: Iterable[T]) -> None:
        super().__init__(
            f'The provided choice "{choice}" is not valid. Valid choices are: {choices}'
        )
