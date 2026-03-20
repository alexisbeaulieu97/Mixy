from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mixy.cli.app import app
from mixy.domain.models import GitSource
from mixy.infrastructure.cache import CacheStore
from mixy.infrastructure.process import GitClient
from mixy.infrastructure.sources.git import GitSourceProvider


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
        }
    )
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _create_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(["init"], cwd=path)
    _run_git(["config", "user.name", "Mixy"], cwd=path)
    _run_git(["config", "user.email", "mixy@example.com"], cwd=path)
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    _run_git(["add", "README.md"], cwd=path)
    _run_git(["commit", "-m", "init"], cwd=path)
    return path


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
    assert cache.has_snapshot(source.url, first.metadata["sha"]) is True


def test_cache_commands_list_and_clear(
    tmp_path: Path,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = CacheStore(tmp_path / "cache")
    cache.get_repo_path("https://example.com/repo.git").mkdir(parents=True)
    snapshot = cache.get_snapshot_path("https://example.com/repo.git", "abc123")
    snapshot.mkdir(parents=True)
    (snapshot / "file.txt").write_text("hello", encoding="utf-8")
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
