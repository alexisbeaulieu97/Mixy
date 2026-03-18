from pathlib import Path

import pygit2
import pytest
from typer.testing import CliRunner

from mixy.cli.app import app
from mixy.domain.models import GitSource
from mixy.infrastructure.cache import CacheStore
from mixy.infrastructure.process import GitClient
from mixy.infrastructure.sources.git import GitSourceProvider


def test_clone_real_local_repo_and_cache_hit(tmp_path: Path) -> None:
    repo = _create_git_repo(tmp_path / "repo")
    cache = CacheStore(tmp_path / "cache")
    client = GitClient()
    provider = GitSourceProvider(git_client=client, cache_store=cache)

    source = GitSource(
        type="git",
        url=str(repo),
        ref="HEAD",
    )

    first = provider.resolve(source)
    first_entries = cache.list_entries()
    second = provider.resolve(source)

    assert first.root_path.exists()
    assert second.root_path == first.root_path
    assert len(first_entries) == 1


def test_cache_commands_list_and_clear(
    tmp_path: Path,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = CacheStore(tmp_path / "cache")
    cache.get_repo_path("https://example.com/repo.git").mkdir(parents=True)
    worktree = cache.get_worktree_path("https://example.com/repo.git", "abc123")
    worktree.mkdir(parents=True)
    (worktree / "file.txt").write_text("hello", encoding="utf-8")
    cache.write_metadata("https://example.com/repo.git", "main", "abc123")

    from mixy.cli.commands import cache as cache_module

    monkeypatch.setattr(cache_module, "CacheStore", lambda: cache)  # type: ignore[arg-type]

    list_result = runner.invoke(app, ["cache", "list"])
    assert list_result.exit_code == 0
    assert "https://example.com/repo.git" in list_result.stdout

    clear_result = runner.invoke(
        app,
        ["cache", "clear", "--url", "https://example.com/repo.git"],
    )
    assert clear_result.exit_code == 0
    assert cache.list_entries() == []


def _create_git_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    repo = pygit2.init_repository(str(path))
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    repo.index.add("README.md")
    repo.index.write()
    tree_id = repo.index.write_tree()
    signature = pygit2.Signature("Mixy", "mixy@example.com")
    repo.create_commit(
        "refs/heads/main",
        signature,
        signature,
        "init",
        tree_id,
        [],
    )
    repo.set_head("refs/heads/main")
    return path
