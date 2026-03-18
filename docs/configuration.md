# Configuration

Mixy reads a YAML config file and validates it into a `ProjectDefinition`.

## Top-level fields

```yaml
version: "1"
name: demo-project
description: Example config
variables: {}
values: {}
sources: []
output:
  path: ./out
  conflict_policy: fail
```

Field summary:

- `version`: required string, currently `"1"`
- `name`: optional string
- `description`: optional string
- `variables`: optional map of variable definitions
- `values`: optional map of project-level variable values
- `sources`: required ordered list of source entries
- `output.path`: output directory path
- `output.conflict_policy`: `fail`, `overwrite`, or `skip` and defaults to `fail`

## Minimal working config

```yaml
version: "1"

sources:
  - id: base
    source:
      type: local_dir
      path: ./template

output:
  path: ./generated
```

## Source entries

Each source entry has an `id` plus a `source` definition.

```yaml
sources:
  - id: base
    source:
      type: local_dir
      path: ./templates/base
```

Optional source entry fields:

- `alias`: label stored in source metadata only
- `enabled`: when `false`, the source is skipped during planning and generation
- `subpath`: reference-level override supported for `local_dir` sources only
- `values`: per-source variable overrides used only when rendering that source
- `merge_strategy`: unsupported and rejected by config validation

## `local_dir` source

Use `local_dir` for a template directory on disk.

```yaml
sources:
  - id: base
    source:
      type: local_dir
      path: ./templates/base
```

You can scope the source to a nested directory:

```yaml
sources:
  - id: api
    source:
      type: local_dir
      path: ./templates/monorepo
    subpath: services/api
```

Reference-level `subpath` is only supported for `local_dir` entries. For git-backed templates, set `subpath` under `source` instead.

## `git` source

Use `git` to read a template from a repository and ref.

```yaml
sources:
  - id: upstream
    source:
      type: git
      url: https://github.com/example/templates.git
      ref: main
      subpath: python/service
```

`local_file` is not part of the supported contract.

If you need to include a single file, place it in a directory and reference that directory with
`local_dir`, or model the file as part of a template directory.

## Variables and values

Declare variable contracts under `variables`:

```yaml
variables:
  project_name:
    type: str
    description: Display name for the generated project
    default: demo
    required: false
  retries:
    type: int
    default: 3
  use_docker:
    type: bool
    default: true
```

Provide project-level values with `values`:

```yaml
values:
  project_name: payments-api
  retries: 5
```

Provide per-source values when a source needs different inputs than the rest:

```yaml
sources:
  - id: api
    values:
      port: 3000
    source:
      type: local_dir
      path: ./templates/api

  - id: docs
    values:
      port: 8080
    source:
      type: local_dir
      path: ./templates/docs
```

## Output and conflict policy

Use `output.path` to choose the destination and `conflict_policy` to control collisions.

```yaml
output:
  path: ./generated
  conflict_policy: fail
```

Policy behavior:

- `fail`: any file conflict stops generation before writes
- `overwrite`: later sources replace earlier ones
- `skip`: later sources are skipped when an earlier source already mapped the output path

File-vs-directory conflicts always fail.

## Complete multi-source example

```yaml
version: "1"
name: team-service
description: Service scaffold assembled from multiple templates

variables:
  project_name:
    type: str
    default: team-service
    required: false
  module_name:
    type: str
    default: team_service
    required: false
  python_version:
    type: str
    default: "3.12"
    required: false
    choices: ["3.11", "3.12", "3.13"]

values:
  python_version: "3.12"

sources:
  - id: base
    source:
      type: local_dir
      path: ./templates/base

  - id: ci
    values:
      python_version: "3.13"
    source:
      type: local_dir
      path: ./templates/ci

  - id: upstream
    source:
      type: git
      url: https://github.com/example/templates.git
      ref: main
      subpath: python-service

output:
  path: ./out/team-service
  conflict_policy: overwrite
```
