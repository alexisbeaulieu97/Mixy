from pathlib import Path
from typing import Union

from pydantic import Field
from typing_extensions import Annotated

from supertemplater.context import Context
from supertemplater.models.base import RenderableBaseModel
from supertemplater.models.directory_dependency import DirectoryDependency
from supertemplater.models.file_dependency import FileDependency
from supertemplater.models.git_dependency import GitDependency
from supertemplater.models.github_dependency import GitHubDependency
from supertemplater.models.project_variables import ProjectVariables
from supertemplater.settings.project_settings import ProjectSettings
from supertemplater.utils import clear_directory

ProjectDependency = Annotated[
    Union[DirectoryDependency, FileDependency, GitDependency, GitHubDependency],
    Field(discriminator="src_type"),
]


class Project(RenderableBaseModel):
    _RENDERABLE_EXCLUDES = {"settings", "variables"}

    dependencies: list[ProjectDependency]
    destination: Path

    settings: ProjectSettings = ProjectSettings()
    variables: ProjectVariables = ProjectVariables()

    @property
    def exists(self) -> bool:
        return self.destination.exists()

    @property
    def is_empty(self) -> bool:
        if not self.exists:
            return True
        return not any(self.destination.iterdir())

    def resolve_dependencies(self, context: Context) -> None:
        self.destination.mkdir(exist_ok=True)
        for dependency in self.dependencies:
            dependency.resolve(self.destination, context)

    def empty(self) -> None:
        if self.exists:
            clear_directory(self.destination)
