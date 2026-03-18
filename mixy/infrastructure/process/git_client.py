"""Git operations wrapper using pygit2 (no PATH dependency)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pygit2

from mixy.domain.exceptions import SourceResolutionError


class GitClient:
    """Perform Git operations via pygit2 without requiring git on PATH."""

    def check_available(self) -> bool:
        """Always True: pygit2 is a Python dependency, not an external binary."""
        return True

    def clone_bare(self, url: str, dest: Path) -> None:
        try:
            pygit2.clone_repository(str(url), str(dest), bare=True)
        except pygit2.GitError as error:
            raise SourceResolutionError(
                f"Failed to clone repository: {url}\n{error}",
                suggestion="Check the URL and your network/SSH credentials.",
            ) from error

    def fetch(self, repo_path: Path) -> None:
        try:
            repo = pygit2.Repository(str(repo_path))
            for remote in repo.remotes:
                remote.fetch()
        except pygit2.GitError as error:
            raise SourceResolutionError(
                f"Failed to fetch repository at {repo_path}: {error}",
                suggestion="Check your network connection and credentials.",
            ) from error

    def rev_parse(self, repo_path: Path, ref: str) -> str:
        try:
            repo = pygit2.Repository(str(repo_path))
            obj = repo.revparse_single(ref)
            return str(obj.peel(pygit2.Commit).id)
        except (pygit2.GitError, KeyError) as error:
            raise SourceResolutionError(
                f"Failed to resolve ref '{ref}' in {repo_path}: {error}",
                suggestion=f"Verify that ref '{ref}' exists in the repository.",
            ) from error

    def extract(self, repo_path: Path, sha: str, dest: Path) -> None:
        try:
            repo = pygit2.Repository(str(repo_path))
            commit = repo.revparse_single(sha).peel(pygit2.Commit)
        except pygit2.GitError as error:
            raise SourceResolutionError(
                f"Failed to read commit {sha} from {repo_path}: {error}",
            ) from error

        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        _write_tree(repo, commit.tree, dest)


def _write_tree(repo: pygit2.Repository, tree: pygit2.Tree, dest: Path) -> None:
    for entry in tree:
        if entry.name is None:
            continue
        path = dest / entry.name
        obj = repo.get(entry.id)
        if obj is None:
            continue
        if isinstance(obj, pygit2.Tree):
            path.mkdir(exist_ok=True)
            _write_tree(repo, obj, path)
        elif isinstance(obj, pygit2.Blob):
            path.write_bytes(obj.data)
