from pathlib import Path
from typing import Literal

from pydantic import validator

from supertemplater.cached_repository import CachedRepository
from supertemplater.context import Context
from supertemplater.settings import settings
from supertemplater.utils import extract_repo_name, is_git_url

from .base import RenderableBaseModel
from .directory_dependency import DirectoryDependency


class GitDependency(RenderableBaseModel):
    src_type: Literal["git"] = "git"
    src: str
    dest: Path
    version: str
    ignores: list[str] = []

    @validator("src")
    def validate_src(cls, v: str) -> str:
        if not is_git_url(v):
            raise ValueError("src must be a git url")
        return v

    @property
    def _repo_cache_path(self) -> Path:
        return settings.dependencies_home.joinpath(extract_repo_name(self.src))

    def resolve(self, into_dir: Path, context: Context) -> None:
        repo = CachedRepository.cache_or_clone(self.src, self._repo_cache_path)
        repo.pull()
        repo.checkout(self.version)
        dependency = DirectoryDependency(
            src=repo.working_tree_dir,  # type: ignore
            dest=self.dest,
            ignores=[".git"] + self.ignores,
        )
        dependency.resolve(into_dir, context)
