"""Git cache management."""

from __future__ import annotations

import json
import shutil
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from platformdirs import user_cache_dir

from mixy.application.settings import AppSettings

CACHE_COMPLETE_FILENAME = ".mixy-cache.complete"
CACHE_METADATA_FILENAME = ".mixy-cache.json"


@dataclass(frozen=True)
class CacheEntry:
    url: str
    ref: str
    sha: str
    size: int


def derive_cache_key(*parts: str) -> str:
    return sha256(":".join(parts).encode("utf-8")).hexdigest()


class CacheStore:
    """Manage cached repositories and extracted snapshots."""

    def __init__(self, root: Path | None = None) -> None:
        configured_root = root or AppSettings.from_env().cache_root
        cache_root = (
            Path(configured_root)
            if configured_root is not None
            else Path(user_cache_dir("mixy"))
        )
        self.root = cache_root
        self.repos_dir = self.root / "repos"
        self.snapshots_dir = self.root / "snapshots"
        self.worktrees_dir = self.snapshots_dir
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def cache_key(*parts: str) -> str:
        return derive_cache_key(*parts)

    def get_repo_path(self, url: str) -> Path:
        return self.repos_dir / self.cache_key("repo", url)

    def get_snapshot_path(self, url: str, sha: str) -> Path:
        return self.snapshots_dir / self.cache_key("snapshot", url, sha)

    def get_worktree_path(self, url: str, sha: str) -> Path:
        return self.get_snapshot_path(url, sha)

    def has_repo(self, url: str) -> bool:
        return self.get_repo_path(url).exists()

    def has_snapshot(self, url: str, sha: str) -> bool:
        snapshot_path = self.get_snapshot_path(url, sha)
        return self._read_snapshot_metadata(snapshot_path) is not None

    def has_worktree(self, url: str, sha: str) -> bool:
        return self.has_snapshot(url, sha)

    def write_metadata(
        self,
        url: str,
        ref: str,
        sha: str,
        snapshot_path: Path | None = None,
    ) -> Path:
        target = (
            Path(snapshot_path)
            if snapshot_path is not None
            else self.get_snapshot_path(url, sha)
        )
        target.mkdir(parents=True, exist_ok=True)

        metadata = {
            "cache_key": self.cache_key(url, sha),
            "ref": ref,
            "sha": sha,
            "url": url,
        }
        metadata_path = target / CACHE_METADATA_FILENAME
        metadata_path.write_text(
            json.dumps(metadata, sort_keys=True),
            encoding="utf-8",
        )
        self._write_completion_marker(target, metadata["cache_key"])
        return target

    def publish_snapshot(self, snapshot_path: Path, url: str, ref: str, sha: str) -> Path:
        staging_path = Path(snapshot_path)
        final_path = self.get_snapshot_path(url, sha)

        self.write_metadata(url, ref, sha, snapshot_path=staging_path)

        if staging_path == final_path:
            return final_path

        if final_path.exists():
            shutil.rmtree(final_path)
        staging_path.replace(final_path)

        return final_path

    def list_entries(self) -> list[CacheEntry]:
        entries: list[CacheEntry] = []

        if not self.snapshots_dir.exists():
            return entries

        for snapshot_path in sorted(
            path for path in self.snapshots_dir.iterdir() if path.is_dir()
        ):
            metadata = self._read_snapshot_metadata(snapshot_path)
            if metadata is None:
                continue

            entries.append(
                CacheEntry(
                    url=metadata["url"],
                    ref=metadata["ref"],
                    sha=metadata["sha"],
                    size=_directory_size(snapshot_path),
                )
            )

        return entries

    def clear_all(self) -> None:
        if self.root.exists():
            shutil.rmtree(self.root)
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def clear_by_url(self, url: str) -> None:
        repo_path = self.get_repo_path(url)
        if repo_path.exists():
            shutil.rmtree(repo_path)

        if not self.snapshots_dir.exists():
            return

        for snapshot_path in self.snapshots_dir.iterdir():
            if not snapshot_path.is_dir():
                continue

            metadata = self._read_snapshot_metadata(snapshot_path, require_completion_marker=False)
            if metadata is None or metadata["url"] != url:
                continue

            shutil.rmtree(snapshot_path, ignore_errors=True)

    @contextmanager
    def snapshot_lock(
        self,
        url: str,
        sha: str,
        *,
        timeout_seconds: float = 30.0,
        poll_interval_seconds: float = 0.05,
    ) -> Iterator[Path]:
        lock_path = self.get_snapshot_path(url, sha).with_name(
            f"{self.get_snapshot_path(url, sha).name}.lock"
        )
        deadline = time.monotonic() + timeout_seconds

        while True:
            try:
                lock_path.mkdir()
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out waiting for cache lock: {lock_path}") from None
                time.sleep(poll_interval_seconds)

        try:
            yield lock_path
        finally:
            shutil.rmtree(lock_path, ignore_errors=True)

    @contextmanager
    def snapshot_staging(self, url: str, sha: str) -> Iterator[Path]:
        prefix = f"{self.cache_key('staging', url, sha)}-"
        staging_path = Path(
            tempfile.mkdtemp(prefix=prefix, dir=str(self.snapshots_dir))
        )
        try:
            yield staging_path
        finally:
            if staging_path.exists():
                shutil.rmtree(staging_path, ignore_errors=True)

    def _read_snapshot_metadata(
        self,
        snapshot_path: Path,
        *,
        require_completion_marker: bool = True,
    ) -> dict[str, str] | None:
        metadata_path = snapshot_path / CACHE_METADATA_FILENAME
        marker_path = snapshot_path / CACHE_COMPLETE_FILENAME
        if not metadata_path.exists():
            return None
        if require_completion_marker and not marker_path.exists():
            return None

        try:
            raw_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return None

        if not isinstance(raw_metadata, dict):
            return None

        cache_key = self._coerce_text(raw_metadata.get("cache_key"))
        url = self._coerce_text(raw_metadata.get("url"))
        ref = self._coerce_text(raw_metadata.get("ref"))
        sha = self._coerce_text(raw_metadata.get("sha"))
        if not all([cache_key, url, ref, sha]):
            return None
        assert cache_key is not None
        assert url is not None
        assert ref is not None
        assert sha is not None

        if cache_key != self.cache_key(url, sha):
            return None

        expected_snapshot_name = self.get_snapshot_path(url, sha).name
        if snapshot_path.name != expected_snapshot_name:
            return None

        if require_completion_marker:
            try:
                marker_contents = marker_path.read_text(encoding="utf-8").strip()
            except OSError:
                return None

            if marker_contents != cache_key:
                return None

        return {
            "cache_key": cache_key,
            "ref": ref,
            "sha": sha,
            "url": url,
        }

    def _write_completion_marker(self, snapshot_path: Path, cache_key: str) -> None:
        marker_path = snapshot_path / CACHE_COMPLETE_FILENAME
        marker_path.write_text(cache_key, encoding="utf-8")

    @staticmethod
    def _coerce_text(value: object) -> str | None:
        if isinstance(value, str) and value:
            return value
        return None


def _directory_size(path: Path) -> int:
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())
