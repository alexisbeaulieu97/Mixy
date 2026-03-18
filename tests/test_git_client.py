"""Tests for GitClient using pygit2 (no subprocess dependency)."""

from pathlib import Path

import pygit2
import pytest

from mixy.domain.exceptions import SourceResolutionError
from mixy.infrastructure.process.git_client import GitClient


def _make_bare_repo(path: Path) -> tuple[pygit2.Repository, str]:
    """Create a local bare repository with one commit.

    Returns (bare_repo, sha_of_commit).
    """
    work_path = path.parent / (path.name + "-work")
    work_path.mkdir()

    repo = pygit2.init_repository(str(work_path))
    (work_path / "hello.txt").write_text("hello world", encoding="utf-8")
    repo.index.add("hello.txt")
    repo.index.write()
    tree = repo.index.write_tree()
    sig = pygit2.Signature("Test", "test@example.com")
    oid = repo.create_commit("refs/heads/main", sig, sig, "init", tree, [])
    repo.set_head("refs/heads/main")

    pygit2.clone_repository(str(work_path), str(path), bare=True)
    return pygit2.Repository(str(path)), str(oid)


def test_git_client_check_available_always_true() -> None:
    client = GitClient()
    assert client.check_available() is True


def test_git_client_clone_bare_creates_repo(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _make_bare_repo(source)

    dest = tmp_path / "clone"
    client = GitClient()
    client.clone_bare(str(source), dest)

    assert dest.exists()
    assert (dest / "HEAD").exists()


def test_git_client_rev_parse_resolves_sha(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _, expected_sha = _make_bare_repo(source)

    client = GitClient()
    sha = client.rev_parse(source, expected_sha)

    assert sha == expected_sha


def test_git_client_rev_parse_raises_for_unknown_ref(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _make_bare_repo(source)

    client = GitClient()
    with pytest.raises(SourceResolutionError):
        client.rev_parse(source, "nonexistent-ref-that-does-not-exist")


def test_git_client_extract_writes_tree_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _, sha = _make_bare_repo(source)

    dest = tmp_path / "extracted"
    client = GitClient()
    client.extract(source, sha, dest)

    assert (dest / "hello.txt").read_text(encoding="utf-8") == "hello world"
