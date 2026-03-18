## Context

Git source support transforms Mixy from a local tool to a team-scale tool. The implementation must be robust against network failures, handle authentication transparently via the user's git config, and cache effectively to avoid repeated clones.

## Goals / Non-Goals

**Goals:**
- Clone or fetch Git repositories into a local cache directory
- Resolve branches/tags to commit SHAs for deterministic caching
- Support subpath extraction (use only a subdirectory of the repo)
- Cache by URL + commit SHA so the same ref at different commits gets fresh content
- Provide `mixy cache list` showing cached entries with sizes
- Provide `mixy cache clear` to remove all or specific cached entries
- Fail clearly if `git` is not installed

**Non-Goals:**
- Git authentication configuration (rely on user's existing git/ssh config)
- Shallow clones (adds complexity for subpath + ref resolution)
- Private repository token management
- Git submodule support
- Monorepo-aware fetching

## Decisions

### Shell out to git rather than using gitpython/pygit2
Shelling out to the `git` CLI avoids heavy native dependencies (libgit2) and leverages the user's existing git configuration (SSH keys, credential helpers, proxy settings). Alternative: gitpython — wraps git CLI anyway. Alternative: pygit2 — requires libgit2 system dependency.

### Clone strategy: bare clone + worktree checkout
Clone repos as bare (`git clone --bare`) into cache, then use `git archive` or `git checkout` to extract the specific ref into a working directory. This saves disk space when multiple refs of the same repo are used. Alternative: full clone per ref — simpler but wastes disk for large repos.

### Cache key: SHA256 of (url + resolved_commit_sha)
The cache key combines the repository URL and the resolved commit SHA. This means:
- Same URL + same commit = cache hit
- Same URL + different commit (branch moved) = cache miss, re-extract
- The bare clone is cached by URL only; the extracted worktree is cached by URL + SHA

### Cache location: platformdirs user_cache_dir
Use `platformdirs.user_cache_dir("mixy")` for the cache root. This follows platform conventions (e.g., `~/.cache/mixy` on Linux). The cache directory structure:
```
~/.cache/mixy/
  repos/          # bare clones keyed by URL hash
  worktrees/      # extracted content keyed by URL+SHA hash
```

### Ref resolution: fetch + rev-parse
For branch/tag refs, run `git fetch` on the bare clone then `git rev-parse <ref>` to get the commit SHA. For SHA refs, verify the SHA exists. This ensures we always work with a concrete commit.

## Risks / Trade-offs

- [Network dependency for first clone] → Cache mitigates subsequent runs; clear error on network failure
- [Bare clone + extraction is more complex than full clone] → Worth it for disk savings with multiple refs
- [No shallow clone support] → Full history is cached; acceptable for template repos which are typically small
- [Git must be installed] → Check at startup, fail with install instructions
