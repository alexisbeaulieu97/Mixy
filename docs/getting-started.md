# Getting Started

Mixy generates a project from one or more template sources described in a YAML config file.

## Requirements

- Python 3.11+
- `pygit2` for `git` sources

## Install from a checkout

With `uv`:

```bash
uv sync
uv run mixy --help
```

With `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
mixy --help
```

If you use `uv`, prefix the command examples in this guide with `uv run`.

## Build a first template

Create a template tree:

```text
template/
  README.md.j2
  src/
    {{ module_name }}.py.j2
```

Add template content:

```md
<!-- template/README.md.j2 -->
# {{ project_name }}

Python version: {{ python_version }}
```

```python
# template/src/{{ module_name }}.py.j2
def main() -> None:
    print("Hello from {{ project_name }}")
```

## Create a config

Create `mixy.yml` next to the template:

```yaml
version: "1"
name: starter
description: First Mixy project

variables:
  project_name:
    type: str
    default: demo-app
    required: false
  module_name:
    type: str
    default: demo_app
    required: false
  python_version:
    type: str
    default: "3.12"
    required: false

sources:
  - id: base
    source:
      type: local_dir
      path: ./template

output:
  path: ./generated
```

Relative paths in the config are resolved relative to the config file itself, not the current
shell directory.

## Validate before generating

```bash
mixy validate mixy.yml
```

Validation catches schema problems such as missing required fields and semantic issues such as
duplicate source ids.

## Preview the output

Use `inspect` to see variables, sources, and the merge preview:

```bash
mixy inspect mixy.yml
```

Use a dry run to preview generation without writing files:

```bash
mixy generate mixy.yml --dry-run
```

## Generate the project

```bash
mixy generate mixy.yml \
  --var project_name=payments-api \
  --var module_name=payments_api
```

Expected output:

```text
generated/
  README.md
  src/
    payments_api.py
```

Successful generation prints a summary with the output path plus counts for created directories,
rendered files, copied files, skipped files, and failures.

## Next steps

- Learn the full config model in [`configuration.md`](configuration.md)
- Learn runtime value precedence in [`variables.md`](variables.md)
- Learn template metadata in [`template-authoring.md`](template-authoring.md)
