from pathlib import Path
from typing import Self

from git.repo import Repo

from mixy.git_manager import GitManager
from mixy.utils import run_github_command


class GitHubManager(GitManager):
    @classmethod
    def cache_or_clone(cls, url: str, dest: Path) -> Self:
        if dest.is_dir():
            return cls(Repo(dest))
        result = run_github_command("repo", "clone", url, dest.as_posix())
        if result.returncode != 0:
            # TODO custom exception
            raise Exception(f"Cloning of repository failed: {url}")
        repo = Repo(dest)
        return cls(repo)
