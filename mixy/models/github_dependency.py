from pathlib import Path
from typing import Literal

from pydantic import validator

from mixy.constants import GITHUB_FORMATS
from mixy.context import Context
from mixy.github_repository import GitHubRepository
from mixy.settings.settings import settings
from mixy.utils import extract_repo_name, is_format

from .base import RenderableBaseModel
from .directory_dependency import DirectoryDependency


class GitHubDependency(RenderableBaseModel):
    src_type: Literal["gh"] = "gh"
    src: str
    dest: Path
    version: str
    ignores: list[str] = []

    @validator("src")
    def validate_src(cls, v: str) -> str:
        if not is_format(v, GITHUB_FORMATS):
            raise ValueError(f"src must be a valid GitHub URL: {GITHUB_FORMATS}")
        return v

    @property
    def _repo_cache_path(self) -> Path:
        return settings.cache.location.joinpath(extract_repo_name(self.src))

    def resolve(self, into_dir: Path, context: Context) -> None:
        repo = GitHubRepository.cache_or_clone(self.src, self._repo_cache_path)
        repo.pull()
        repo.checkout(self.version)
        dependency = DirectoryDependency(
            src=repo.location,  # type: ignore
            dest=self.dest,
            ignores=[".git"] + self.ignores,
        )
        dependency.resolve(into_dir, context)
