# Git and Cache

Mixy can resolve template sources from Git repositories and cache extracted worktrees locally.

## Git source example

```yaml
sources:
  - id: upstream
    source:
      type: git
      url: https://github.com/example/templates.git
      ref: main
```

Use `subpath` to target a directory inside the repository:

```yaml
sources:
  - id: upstream
    source:
      type: git
      url: https://github.com/example/templates.git
      ref: v1.2.0
      subpath: python/service
```

Requirements:

- `ref` can be a branch, tag, or commit that the Git integration can resolve
- Mixy uses its Python-backed Git integration path rather than shelling out to `git`

If the configured `subpath` does not exist at the resolved revision, Mixy fails with a
source-resolution error.

## What gets cached

Mixy caches two things:

- a bare clone for each repository URL
- extracted worktrees for resolved commit SHAs

The cache root comes from `platformdirs`. On Linux it is typically:

```text
~/.cache/mixy
```

The cache contains:

```text
repos/
worktrees/
```

Each extracted worktree also stores metadata with the URL, ref, and resolved SHA.

## Listing cache entries

```bash
mixy cache list
```

The command prints:

- repository URL
- ref used when the worktree was written
- resolved commit SHA
- cached size in bytes

## Clearing cache

Clear everything:

```bash
mixy cache clear
```

Clear only one repository URL:

```bash
mixy cache clear --url https://github.com/example/templates.git
```

## Example workflow

```yaml
version: "1"

variables:
  project_name:
    type: str
    default: payments-api
    required: false

sources:
  - id: upstream
    source:
      type: git
      url: https://github.com/example/templates.git
      ref: main
      subpath: python/service

output:
  path: ./generated
```

```bash
mixy validate mixy.yml
mixy inspect mixy.yml
mixy generate mixy.yml
mixy cache list
```
