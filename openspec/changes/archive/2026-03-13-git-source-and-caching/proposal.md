## Why

Git repositories are the primary way teams share templates across projects and organizations. Without Git source support, Mixy is limited to local directories, which prevents the core use case of composing reusable templates from version-controlled repositories. Caching avoids re-cloning on every generation.

## What Changes

- Implement `GitSourceProvider` that resolves Git source definitions by cloning/fetching repositories
- Shell out to `git` CLI for clone, fetch, and checkout operations
- Support ref specification: branch names, tags, and commit SHAs
- Support subpath extraction from a cloned repository
- Implement `CacheStore` using platformdirs for cache directory management
- Cache cloned repositories keyed by URL + resolved commit SHA
- Implement `mixy cache list` and `mixy cache clear` CLI commands
- Verify `git` is available at startup and fail with a clear message if not

## Capabilities

### New Capabilities
- `git-source`: Git repository source provider with clone/fetch, ref resolution, subpath extraction, and git availability checking
- `source-caching`: Local cache store for materialized sources using platformdirs, with list and clear management commands

### Modified Capabilities

## Impact

- Creates `mixy/infrastructure/sources/git.py`
- Creates `mixy/infrastructure/process/git_client.py`
- Creates `mixy/infrastructure/cache/cache_store.py`
- Adds `cache` command group to CLI
- Registers GitSourceProvider in the provider registry
