from functools import cached_property
from pathlib import Path
from typing import Literal

from git.repo import Repo
from pydantic import validator

from supertemplater.context import Context
from supertemplater.utils import extract_repo_name, is_git_url

from .base import RenderableBaseModel
from .config import config
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

    @cached_property
    def name(self) -> str:
        return extract_repo_name(self.src)

    @cached_property
    def repo(self) -> Repo:
        if config.home.joinpath(self.name).is_dir():
            return Repo(config.home.joinpath(self.name))

        return self._clone()

    @property
    def needs_update(self) -> bool:
        self.fetch()
        commits_behind = self.repo.iter_commits(
            f"{self.branch}..{self.tracking_branch}"
        )
        return next(commits_behind, None) is not None

    @property
    def branch(self) -> str:
        return self.repo.active_branch.name

    @property
    def tracking_branch(self) -> str | None:
        tracking_branch = self.repo.active_branch.tracking_branch()
        if tracking_branch is None:
            return None
        return tracking_branch.name

    def pull(self) -> None:
        self.repo.remotes.origin.pull()

    def fetch(self) -> None:
        self.repo.remotes.origin.fetch()

    def _clone(self) -> Repo:
        if self.version is None:
            return Repo.clone_from(self.src, config.home.joinpath(self.name), depth=1)  # type: ignore
        return Repo.clone_from(self.src, config.home.joinpath(self.name), branch=self.version, depth=1)  # type: ignore

    def resolve(self, into_dir: Path, context: Context) -> None:
        if self.needs_update:
            self.pull()
        dependency = DirectoryDependency(
            src=self.repo.working_dir, dest=self.dest, ignores=[".git"] + self.ignores
        )
        dependency.resolve(into_dir, context)
