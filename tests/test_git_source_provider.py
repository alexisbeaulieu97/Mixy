from pathlib import Path

import pytest

from mixy.domain.exceptions import SourceResolutionError
from mixy.domain.models import GitSource
from mixy.infrastructure.cache import CacheStore
from mixy.infrastructure.process import GitClient
from mixy.infrastructure.sources.git import GitSourceProvider


class RecordingGitClient(GitClient):
    def __init__(self, sha: str = "abc123") -> None:
        self.sha = sha
        self.calls: list[str] = []

    def check_available(self) -> bool:
        self.calls.append("check_available")
        return True

    def clone_bare(self, url: str, dest: Path) -> None:
        self.calls.append("clone_bare")
        dest.mkdir(parents=True, exist_ok=True)

    def fetch(self, repo_path: Path) -> None:
        self.calls.append("fetch")

    def rev_parse(self, repo_path: Path, ref: str) -> str:
        self.calls.append("rev_parse")
        return self.sha

    def extract(self, repo_path: Path, sha: str, dest: Path) -> None:
        self.calls.append("extract")
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "template").mkdir(exist_ok=True)
        (dest / "template" / "README.md").write_text("hello", encoding="utf-8")


def test_git_source_provider_dispatch_and_subpath(tmp_path: Path) -> None:
    store = CacheStore(tmp_path)
    client = RecordingGitClient()
    provider = GitSourceProvider(git_client=client, cache_store=store)
    source = GitSource(
        type="git",
        url="https://example.com/repo.git",
        ref="main",
        subpath="template",
    )

    assert provider.can_handle(source) is True
    resolved = provider.resolve(source)

    assert resolved.root_path.name == "template"
    assert "extract" in client.calls


def test_git_source_provider_reuses_cached_worktree(tmp_path: Path) -> None:
    store = CacheStore(tmp_path)
    client = RecordingGitClient()
    provider = GitSourceProvider(git_client=client, cache_store=store)
    source = GitSource(type="git", url="https://example.com/repo.git", ref="main")

    provider.resolve(source)
    first_extract_count = client.calls.count("extract")
    provider.resolve(source)

    assert client.calls.count("extract") == first_extract_count


def test_git_source_provider_rejects_missing_subpath(tmp_path: Path) -> None:
    store = CacheStore(tmp_path)
    client = RecordingGitClient()
    provider = GitSourceProvider(git_client=client, cache_store=store)
    source = GitSource(
        type="git",
        url="https://example.com/repo.git",
        ref="main",
        subpath="missing",
    )

    with pytest.raises(SourceResolutionError):
        provider.resolve(source)
