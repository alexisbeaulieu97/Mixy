## 1. Git Client

- [x] 1.1 Create `mixy/infrastructure/process/git_client.py` with `GitClient` class
- [x] 1.2 Implement `check_available() -> bool` — verify git is on PATH
- [x] 1.3 Implement `clone_bare(url: str, dest: Path)` — bare clone
- [x] 1.4 Implement `fetch(repo_path: Path)` — fetch updates on bare clone
- [x] 1.5 Implement `rev_parse(repo_path: Path, ref: str) -> str` — resolve ref to SHA
- [x] 1.6 Implement `extract(repo_path: Path, sha: str, dest: Path)` — extract commit content to directory
- [x] 1.7 Handle subprocess errors with clear error messages

## 2. Cache Store

- [x] 2.1 Create `mixy/infrastructure/cache/cache_store.py` with `CacheStore` class
- [x] 2.2 Implement cache directory layout: `repos/` for bare clones, `worktrees/` for extracted content
- [x] 2.3 Implement `get_repo_path(url: str) -> Path` — SHA256 hash of URL
- [x] 2.4 Implement `get_worktree_path(url: str, sha: str) -> Path` — SHA256 hash of URL+SHA
- [x] 2.5 Implement `has_repo(url: str) -> bool` and `has_worktree(url: str, sha: str) -> bool`
- [x] 2.6 Implement `list_entries() -> list[CacheEntry]` with URL, ref, SHA, size
- [x] 2.7 Implement `clear_all()` and `clear_by_url(url: str)`
- [x] 2.8 Use `platformdirs.user_cache_dir("mixy")` for cache root

## 3. Git Source Provider

- [x] 3.1 Create `mixy/infrastructure/sources/git.py` with `GitSourceProvider`
- [x] 3.2 Implement `can_handle` — returns True for `git` type
- [x] 3.3 Implement `resolve` — check git available, clone/fetch, resolve ref, extract, handle subpath
- [x] 3.4 Implement `fingerprint` — hash of URL + resolved SHA
- [x] 3.5 Register GitSourceProvider in the source resolver registry

## 4. CLI Cache Commands

- [x] 4.1 Create `mixy/cli/commands/cache.py` with Typer subcommand group
- [x] 4.2 Implement `mixy cache list` — display cached entries table
- [x] 4.3 Implement `mixy cache clear` with optional `--url` filter
- [x] 4.4 Register cache command group in main CLI app

## 5. Tests

- [x] 5.1 Unit test GitClient — mock subprocess calls, verify commands constructed correctly
- [x] 5.2 Unit test CacheStore — path hashing, has_repo, has_worktree, list, clear
- [x] 5.3 Unit test GitSourceProvider — dispatch, resolve flow, subpath handling
- [x] 5.4 Integration test: clone a real small test repo and verify extracted content
- [x] 5.5 Integration test: cache hit on second resolve
- [x] 5.6 Integration test: cache list and cache clear commands
