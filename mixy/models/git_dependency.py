from functools import cached_property
from pathlib import Path
from typing import Literal, Type

from mixy.context import Context
from mixy.git_manager import GitManager
from mixy.github_manager import GitHubManager
from mixy.models.base import RenderableBaseModel
from mixy.models.directory_dependency import DirectoryDependency
from mixy.protocols.git_manager_protocol import GitManagerProtocol
from mixy.settings.settings import settings
from mixy.utils import extract_repo_name

git_managers: dict[str, Type[GitManagerProtocol]] = {
    "git": GitManager,
    "gh": GitHubManager,
}


class GitDependency(RenderableBaseModel):
    src_type: Literal["git", "gh"]
    src: str
    version: str
    dest: Path = Path("/")
    ignores: list[str] = []

    @cached_property
    def _git_manager_class(self) -> Type[GitManagerProtocol]:
        return git_managers[self.src_type]

    @property
    def _repo_cache_path(self) -> Path:
        return settings.cache.location.joinpath(extract_repo_name(self.src))

    def resolve(self, into_dir: Path, context: Context) -> None:
        manager = self._git_manager_class.cache_or_clone(
            self.src, self._repo_cache_path
        )
        manager.pull()
        manager.checkout(self.version)
        if manager.location is not None:
            dependency = DirectoryDependency(
                src=manager.location,
                dest=self.dest,
                ignores=[".git"] + self.ignores,
            )
            dependency.resolve(into_dir, context)
