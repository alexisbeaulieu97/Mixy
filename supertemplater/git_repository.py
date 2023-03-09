from pathlib import Path
from typing import Self

from git.repo import Repo


class GitRepository(Repo):
    def is_branch_behind(self, branch: str) -> bool:
        local_branch = self.heads[branch]
        remote_branch = local_branch.tracking_branch()
        if remote_branch is None:
            return False
        self.remote().fetch()
        commits_behind = self.iter_commits(f"{local_branch}..{remote_branch}")
        return next(commits_behind, None) is not None

    @property
    def location(self) -> Path | None:
        loc = self.working_tree_dir
        return None if loc is None else Path(loc)

    @classmethod
    def cache_or_clone(cls, url: str, dest: Path) -> Self:
        if dest.is_dir():
            return cls(dest)
        repo = cls.clone_from(url, dest)
        return cls(repo.common_dir)

    def checkout(self, version: str) -> None:
        self.git.checkout(version)

    def fetch(self, tags: bool = True) -> None:
        self.remotes.origin.fetch(tags=tags)

    def pull(self, tags: bool = True) -> None:
        if self.head.is_detached:
            self.git.checkout("-")
        self.remotes.origin.pull(tags=tags)

    def sync(self) -> None:
        self.fetch()
        if self.is_branch_behind(self.active_branch.name):
            self.pull()
