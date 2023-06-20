from pathlib import Path
from typing import Union

from pydantic import Field
from typing_extensions import Annotated

from mixy.context import Context
from mixy.models.base import RenderableBaseModel
from mixy.models.directory_dependency import DirectoryDependency
from mixy.models.file_dependency import FileDependency
from mixy.models.git_dependency import GitDependency
from mixy.models.mixy_dependency import MixyDependency
from mixy.models.template_var import TemplateVar
from mixy.settings.project_settings import ProjectSettings
from mixy.utils import clear_directory

ProjectDependency = Annotated[
    Union[
        DirectoryDependency,
        FileDependency,
        GitDependency,
        MixyDependency,
    ],
    Field(discriminator="src_type"),
]


class Project(RenderableBaseModel):
    _RENDERABLE_EXCLUDES = {"settings", "vars"}

    dependencies: list[ProjectDependency]
    destination: Path

    settings: ProjectSettings = ProjectSettings()
    vars: dict[str, TemplateVar] = {}

    @property
    def exists(self) -> bool:
        return self.destination.exists()

    @property
    def is_empty(self) -> bool:
        if not self.exists:
            return True
        return not any(self.destination.iterdir())

    def create(self, context: Context) -> None:
        context = Context.derive_from(context, **self.vars)
        self.render(context)
        self.destination.mkdir(exist_ok=True)
        for dependency in self.dependencies:
            dependency.resolve(self.destination, context)

    def empty(self) -> None:
        if self.exists:
            clear_directory(self.destination)
