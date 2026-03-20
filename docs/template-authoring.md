# Template Authoring

Mixy templates are normal files and directories with optional Jinja expressions and optional
metadata files.

## Basic rendering

Files ending in `.j2` are rendered as templates and written without the `.j2` suffix.

Example source tree:

```text
template/
  README.md.j2
  src/
    {{ module_name }}.py.j2
```

Example file:

```md
# {{ project_name }}
```

With:

```yaml
variables:
  project_name:
    type: str
    default: demo
    required: false
  module_name:
    type: str
    default: demo_app
    required: false
```

The output becomes:

```text
README.md
src/demo_app.py
```

## Path rendering

Path segments are rendered by default.

Example:

```text
template/
  services/
    {{ module_name }}/
      __init__.py.j2
```

With `module_name=payments_api`, Mixy writes:

```text
services/payments_api/__init__.py
```

## Binary and raw files

Mixy treats common binary extensions and files containing null bytes as binary. Binary files are
copied as-is and are never rendered.

Examples of common binary extensions detected by default include:

- `.png`
- `.jpg`
- `.gif`
- `.woff2`
- `.zip`

## Directory metadata: `.mixy/template.yml`

Use `.mixy/template.yml` to apply metadata to a directory subtree.

Example layout:

```text
template/
  .mixy/
    template.yml
  README.md.j2
  docs/
    guide.md
```

Example metadata:

```yaml
description: Root template metadata
copy_mode: render
render:
  path_names: true
  text_files: true
exclude:
  - "*.png"
defaults:
  project_name: demo
variables:
  project_name:
    type: str
    required: false
    default: demo
```

Supported metadata fields:

- `description`
- `copy_mode`
- `render`
- `include`
- `exclude`
- `defaults`
- `variables`

Jinja undefined variables are handled strictly by default. There is no `render.undefined`
metadata setting in the current contract.

Disallowed metadata fields:

- `source`
- `output`
- `cache`
- `merge_strategy`
- `hooks`
- `imports`

## File metadata sidecars: `*.mixy.yml`

Use a sidecar file to target one file only.

Example:

```text
template/
  Dockerfile
  Dockerfile.mixy.yml
```

```yaml
copy_mode: raw
```

This applies only to `Dockerfile`.

Sidecars also work for `.j2` files:

```text
config.yaml.j2
config.yaml.j2.mixy.yml
```

## Metadata inheritance

Mixy resolves metadata in this order:

1. project defaults from the config
2. source root `.mixy/template.yml`
3. nested directory `.mixy/template.yml`
4. file sidecar `*.mixy.yml`

Nearest scope wins for scalar fields such as `copy_mode` and render flags.

Example:

```text
template/
  .mixy/template.yml
  src/
    .mixy/template.yml
    main.py.j2
```

Root metadata:

```yaml
render:
  path_names: true
  text_files: true
exclude:
  - "*.png"
```

Nested metadata:

```yaml
render:
  path_names: false
exclude:
  - "*.jpg"
```

Effective result under `src/`:

- `render.path_names` becomes `false`
- `exclude` becomes `["*.png", "*.jpg"]`

To replace a list instead of unioning it, use `_replace: true`:

```yaml
exclude:
  items:
    - "*.gif"
  _replace: true
```

## Variable refinement in metadata

Metadata can add or refine variable definitions, but the refinement must stay compatible with the
parent definition.

Valid refinement:

```yaml
variables:
  project_name:
    type: str
    description: Friendly project name
```

Invalid refinements include:

- changing the variable type
- changing the `secret` flag
- making an optional parent variable required
- introducing `choices` that are not a subset of the parent choices

## Metadata files are not copied

Mixy excludes `.mixy/` directories and `*.mixy.yml` files from generated output.
