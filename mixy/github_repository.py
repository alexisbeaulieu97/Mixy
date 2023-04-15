from dataclasses import dataclass
from pathlib import Path
from typing import Self

from mixy.git_repository import GitRepository
from mixy.utils import run_github_command


@dataclass
class GitHubRepository:
    repo: GitRepository

    @property
    def location(self) -> Path | None:
        return self.repo.location

    @classmethod
    def cache_or_clone(cls, url: str, dest: Path) -> Self:
        if dest.is_dir():
            return cls(GitRepository(dest))
        result = run_github_command("repo", "clone", url, dest.as_posix())
        if result.returncode != 0:
            # TODO custom exception
            raise Exception(f"Cloning of repository failed: {url}")
        repo = GitRepository(dest)
        return cls(repo)

    def checkout(self, version: str) -> None:
        self.repo.checkout(version)

    def fetch(self, tags: bool = True) -> None:
        self.repo.fetch(tags)

    def pull(self, tags: bool = True) -> None:
        self.repo.pull(tags)

    def sync(self) -> None:
        self.repo.sync()
