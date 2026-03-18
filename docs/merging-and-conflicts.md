# Merging and Conflicts

Mixy merges sources in the order they appear in `sources`.

## Source order matters

Example:

```yaml
sources:
  - id: base
    source:
      type: local_dir
      path: ./templates/base

  - id: docker
    source:
      type: local_dir
      path: ./templates/docker
```

If both sources map a file to the same output path, Mixy treats that as a file conflict.

## Conflict policies

Configure the behavior under `output.conflict_policy`.

### `fail`

Stop before writing files when there is a file conflict.

```yaml
output:
  path: ./generated
  conflict_policy: fail
```

This is the default.

### `overwrite`

Let later sources replace earlier ones.

```yaml
output:
  path: ./generated
  conflict_policy: overwrite
```

Equivalent one-off override:

```bash
mixy generate mixy.yml --overwrite
```

### `skip`

Keep the earlier file and skip the later one.

```yaml
output:
  path: ./generated
  conflict_policy: skip
```

With `skip`, the first source that maps an output path wins.

## File-vs-directory conflicts

If one source maps a file to a path that another source needs as a directory, Mixy always fails.

Example:

- source A produces `docs`
- source B produces `docs/index.md`

This cannot be resolved with `overwrite` or `skip`.

## Preview conflicts before writing

Use `inspect` to preview the merged output:

```bash
mixy inspect mixy.yml
```

Use a dry run to preview planned actions:

```bash
mixy generate mixy.yml --dry-run
```

Dry-run output is a simple table-like report:

```text
Action | Output Path | Source
create_dir | generated | -
RenderTemplate | generated/README.md | base
CopyRaw | generated/logo.png | base
```

When conflicts exist in dry-run mode, Mixy prints a `Conflicts:` section instead of writing
files.

## Example: layering sources

This is a common pattern:

```yaml
version: "1"

sources:
  - id: base
    source:
      type: local_dir
      path: ./templates/base

  - id: python
    source:
      type: local_dir
      path: ./templates/python

  - id: ci
    source:
      type: local_dir
      path: ./templates/ci

output:
  path: ./generated
  conflict_policy: overwrite
```

In that layout:

- `base` provides the broad scaffold
- `python` customizes language-specific files
- `ci` adds or replaces workflow files

Choose `overwrite` when later sources are intentionally refining earlier ones. Choose `fail` when
you want collisions to be explicit.
