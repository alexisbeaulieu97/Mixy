"""Git-backed source provider."""

from __future__ import annotations

from hashlib import sha256

from mixy.domain.exceptions import SourceResolutionError
from mixy.domain.models import GitSource, MaterializedSource, SourceDefinition
from mixy.infrastructure.cache import CacheStore
from mixy.infrastructure.process import GitClient


class GitSourceProvider:
    """Resolve git sources through a bare-clone cache."""

    def __init__(
        self,
        *,
        git_client: GitClient | None = None,
        cache_store: CacheStore | None = None,
    ) -> None:
        self._git = git_client or GitClient()
        self._cache = cache_store or CacheStore()

    def can_handle(self, source: SourceDefinition) -> bool:
        return source.type == "git"

    def resolve(self, source: SourceDefinition) -> MaterializedSource:
        if not isinstance(source, GitSource):
            raise SourceResolutionError(
                f'GitSourceProvider cannot resolve source type "{source.type}".',
                suggestion="Use a `git` source with `url` and `ref` fields.",
            )
        if not self._git.check_available():
            raise SourceResolutionError(
                "Git is not available on PATH. Install git to use git sources.",
                suggestion="Install git and retry.",
                system_error=True,
            )

        repo_path = self._cache.get_repo_path(source.url)
        if self._cache.has_repo(source.url):
            self._git.fetch(repo_path)
        else:
            self._git.clone_bare(source.url, repo_path)

        sha = self._git.rev_parse(repo_path, source.ref)
        worktree_path = self._cache.get_worktree_path(source.url, sha)
        if not self._cache.has_worktree(source.url, sha):
            self._git.extract(repo_path, sha, worktree_path)
            self._cache.write_metadata(source.url, source.ref, sha)

        root_path = worktree_path
        if source.subpath:
            root_path = worktree_path / source.subpath
            if not root_path.exists():
                raise SourceResolutionError(
                    f'Git source subpath does not exist: "{source.subpath}" '
                    f'in "{source.url}@{sha}".',
                    suggestion="Check the configured subpath and ref for this git source.",
                )

        return MaterializedSource(
            root_path=root_path.resolve(),
            source_id=source.url,
            fingerprint=self.fingerprint(source),
            metadata={"provider": "git", "sha": sha, "url": source.url},
        )

    def fingerprint(self, source: SourceDefinition) -> str:
        if not isinstance(source, GitSource):
            raise SourceResolutionError(
                f'GitSourceProvider cannot fingerprint source type "{source.type}".',
                suggestion="Use a `git` source with `url` and `ref` fields.",
            )
        repo_path = self._cache.get_repo_path(source.url)
        if not self._cache.has_repo(source.url):
            self._git.clone_bare(source.url, repo_path)
        else:
            self._git.fetch(repo_path)
        sha = self._git.rev_parse(repo_path, source.ref)
        return sha256(f"{source.url}:{sha}".encode()).hexdigest()
