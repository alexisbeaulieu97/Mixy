"""Tests for GitClient using the git CLI."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from mixy.domain.exceptions import SourceResolutionError
from mixy.infrastructure.process.git_client import GitClient


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


def _make_repo(path: Path) -> str:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(["init"], cwd=path)
    _run_git(["config", "user.name", "Test"], cwd=path)
    _run_git(["config", "user.email", "test@example.com"], cwd=path)
    (path / "hello.txt").write_text("hello world", encoding="utf-8")
    _run_git(["add", "hello.txt"], cwd=path)
    _run_git(["commit", "-m", "init"], cwd=path)
    return _run_git(["rev-parse", "HEAD"], cwd=path).stdout.strip()


def test_git_client_check_available_always_true() -> None:
    client = GitClient()
    assert client.check_available() is True


def test_git_client_clone_bare_creates_repo(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _make_repo(source)

    dest = tmp_path / "clone"
    client = GitClient()
    client.clone_bare(str(source), dest)

    assert dest.exists()
    assert (dest / "HEAD").exists()


def test_git_client_rev_parse_resolves_sha(tmp_path: Path) -> None:
    source = tmp_path / "source"
    expected_sha = _make_repo(source)
    bare_repo = tmp_path / "bare"

    client = GitClient()
    client.clone_bare(str(source), bare_repo)

    sha = client.rev_parse(bare_repo, expected_sha)

    assert sha == expected_sha


def test_git_client_rev_parse_raises_for_unknown_ref(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _make_repo(source)
    bare_repo = tmp_path / "bare"

    client = GitClient()
    client.clone_bare(str(source), bare_repo)

    with pytest.raises(SourceResolutionError):
        client.rev_parse(bare_repo, "nonexistent-ref-that-does-not-exist")


def test_git_client_extract_writes_tree_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    sha = _make_repo(source)
    bare_repo = tmp_path / "bare"

    client = GitClient()
    client.clone_bare(str(source), bare_repo)

    dest = tmp_path / "extracted"
    client.extract(bare_repo, sha, dest)

    assert (dest / "hello.txt").read_text(encoding="utf-8") == "hello world"
