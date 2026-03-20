"""Git-backed source provider."""

from __future__ import annotations

from pathlib import Path

from mixy.domain.exceptions import SourceResolutionError
from mixy.domain.models import GitSource, MaterializedSource, SourceDefinition
from mixy.infrastructure.cache import CacheStore
from mixy.infrastructure.process import GitClient


class GitSourceProvider:
    """Resolve git sources through a bare-clone cache."""

    provider_id = "git"

    def __init__(
        self,
        *,
        git_client: GitClient | None = None,
        cache_store: CacheStore | None = None,
    ) -> None:
        self._git: GitClient | None = git_client
        self._cache: CacheStore | None = cache_store

    def can_handle(self, source: SourceDefinition) -> bool:
        return source.type == "git"

    def resolve(self, source: SourceDefinition) -> MaterializedSource:
        if not isinstance(source, GitSource):
            raise SourceResolutionError(
                f'GitSourceProvider cannot resolve source type "{source.type}".',
                suggestion="Use a `git` source with `url` and `ref` fields.",
            )

        repo_path, sha = self._ensure_repo(source)
        fingerprint = self.cache_store.cache_key(source.url, sha)

        snapshot_path = self.cache_store.get_snapshot_path(source.url, sha)
        with self.cache_store.snapshot_lock(source.url, sha):
            if not self.cache_store.has_snapshot(source.url, sha):
                with self.cache_store.snapshot_staging(source.url, sha) as staging_path:
                    self.git_client.extract(repo_path, sha, staging_path)
                    snapshot_path = self.cache_store.publish_snapshot(
                        staging_path,
                        source.url,
                        source.ref,
                        sha,
                    )

        root_path = snapshot_path
        if source.subpath:
            root_path = snapshot_path / source.subpath
            if not root_path.exists():
                raise SourceResolutionError(
                    f'Git source subpath does not exist: "{source.subpath}" '
                    f'in "{source.url}@{sha}".',
                    suggestion="Check the configured subpath and ref for this git source.",
                )

        return MaterializedSource(
            root_path=root_path.resolve(),
            source_id=source.url,
            fingerprint=fingerprint,
            metadata={"provider": "git", "sha": sha, "url": source.url},
        )

    def fingerprint(self, source: SourceDefinition) -> str:
        if not isinstance(source, GitSource):
            raise SourceResolutionError(
                f'GitSourceProvider cannot fingerprint source type "{source.type}".',
                suggestion="Use a `git` source with `url` and `ref` fields.",
            )
        _, sha = self._ensure_repo(source)
        return self.cache_store.cache_key(source.url, sha)

    def _ensure_repo(self, source: GitSource) -> tuple[Path, str]:
        """Fetch or clone the bare repo and return (repo_path, resolved_sha)."""
        repo_path = self.cache_store.get_repo_path(source.url)
        if self.cache_store.has_repo(source.url):
            self.git_client.fetch(repo_path)
        else:
            self.git_client.clone_bare(source.url, repo_path)
        sha = self.git_client.rev_parse(repo_path, source.ref)
        return repo_path, sha

    @property
    def git_client(self) -> GitClient:
        if self._git is None:
            self._git = GitClient()
        return self._git

    @property
    def cache_store(self) -> CacheStore:
        if self._cache is None:
            self._cache = CacheStore()
        return self._cache
