"""Git cache management."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from platformdirs import user_cache_dir


@dataclass(frozen=True, slots=True)
class CacheEntry:
    url: str
    ref: str
    sha: str
    size: int


class CacheStore:
    """Manage cached repositories and extracted worktrees."""

    def __init__(self, root: Path | None = None) -> None:
        cache_root = Path(root) if root is not None else Path(user_cache_dir("mixy"))
        self.root = cache_root
        self.repos_dir = self.root / "repos"
        self.worktrees_dir = self.root / "worktrees"
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

    def get_repo_path(self, url: str) -> Path:
        return self.repos_dir / sha256(url.encode()).hexdigest()

    def get_worktree_path(self, url: str, sha: str) -> Path:
        return self.worktrees_dir / sha256(f"{url}:{sha}".encode()).hexdigest()

    def has_repo(self, url: str) -> bool:
        return self.get_repo_path(url).exists()

    def has_worktree(self, url: str, sha: str) -> bool:
        return self.get_worktree_path(url, sha).exists()

    def write_metadata(self, url: str, ref: str, sha: str) -> None:
        worktree = self.get_worktree_path(url, sha)
        worktree.mkdir(parents=True, exist_ok=True)
        metadata_path = worktree / ".mixy-cache.json"
        metadata_path.write_text(
            json.dumps({"ref": ref, "sha": sha, "url": url}, sort_keys=True),
            encoding="utf-8",
        )

    def list_entries(self) -> list[CacheEntry]:
        entries: list[CacheEntry] = []

        for worktree in sorted(path for path in self.worktrees_dir.iterdir() if path.is_dir()):
            metadata_path = worktree / ".mixy-cache.json"
            if not metadata_path.exists():
                continue

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            entries.append(
                CacheEntry(
                    url=str(metadata["url"]),
                    ref=str(metadata["ref"]),
                    sha=str(metadata["sha"]),
                    size=_directory_size(worktree),
                )
            )

        return entries

    def clear_all(self) -> None:
        if self.root.exists():
            shutil.rmtree(self.root)
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

    def clear_by_url(self, url: str) -> None:
        repo_path = self.get_repo_path(url)
        if repo_path.exists():
            shutil.rmtree(repo_path)

        for entry in self.list_entries():
            if entry.url == url:
                worktree = self.get_worktree_path(entry.url, entry.sha)
                if worktree.exists():
                    shutil.rmtree(worktree)


def _directory_size(path: Path) -> int:
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())
