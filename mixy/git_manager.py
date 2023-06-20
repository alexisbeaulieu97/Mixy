from dataclasses import dataclass
from pathlib import Path
from typing import Self

from git.repo import Repo


@dataclass
class GitManager:
    repo: Repo

    @property
    def location(self) -> Path | None:
        loc = self.repo.working_tree_dir
        return None if loc is None else Path(loc)

    @classmethod
    def cache_or_clone(cls, url: str, dest: Path) -> Self:
        if dest.is_dir():
            return cls(Repo(dest))
        repo = Repo.clone_from(url, dest)
        return cls(repo)

    def checkout(self, version: str) -> None:
        self.repo.git.checkout(version)

    def fetch(self, tags: bool = True) -> None:
        self.repo.remotes.origin.fetch(tags=tags)

    def pull(self, tags: bool = True) -> None:
        if self.repo.head.is_detached:
            self.repo.git.checkout("-")
        self.repo.remotes.origin.pull(tags=tags)
