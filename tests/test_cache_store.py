from pathlib import Path

from mixy.infrastructure.cache import CacheStore


def test_cache_store_hashes_paths_and_tracks_entries(tmp_path: Path) -> None:
    store = CacheStore(tmp_path)
    url = "https://example.com/repo.git"
    sha = "abc123"

    repo_path = store.get_repo_path(url)
    snapshot_path = store.get_snapshot_path(url, sha)
    repo_path.mkdir(parents=True)
    snapshot_path.mkdir(parents=True)
    (snapshot_path / "file.txt").write_text("hello", encoding="utf-8")
    store.write_metadata(url, "main", sha)

    assert store.has_repo(url) is True
    assert store.has_snapshot(url, sha) is True
    entries = store.list_entries()
    assert len(entries) == 1
    assert entries[0].url == url
    assert entries[0].sha == sha


def test_cache_store_ignores_incomplete_or_invalid_snapshots(tmp_path: Path) -> None:
    store = CacheStore(tmp_path)
    url = "https://example.com/repo.git"
    sha = "abc123"
    incomplete_snapshot = store.get_snapshot_path(url, sha)
    incomplete_snapshot.mkdir(parents=True)
    (incomplete_snapshot / ".mixy-cache.json").write_text(
        "{}",
        encoding="utf-8",
    )

    invalid_snapshot = store.get_snapshot_path(url, "def456")
    invalid_snapshot.mkdir(parents=True)
    store.write_metadata(url, "main", "def456")
    (invalid_snapshot / ".mixy-cache.complete").write_text("wrong-key", encoding="utf-8")

    assert store.list_entries() == []
    assert store.has_snapshot(url, sha) is False
    assert store.has_snapshot(url, "def456") is False


def test_cache_store_clear_methods(tmp_path: Path) -> None:
    store = CacheStore(tmp_path)
    url = "https://example.com/repo.git"
    sha = "abc123"

    store.get_repo_path(url).mkdir(parents=True)
    store.get_snapshot_path(url, sha).mkdir(parents=True)
    store.write_metadata(url, "main", sha)
    store.clear_by_url(url)
    assert store.has_repo(url) is False
    assert store.list_entries() == []

    store.get_repo_path(url).mkdir(parents=True)
    store.clear_all()
    assert set(store.root.iterdir()) == {store.repos_dir, store.snapshots_dir}
