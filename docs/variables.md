# Variables

Mixy resolves variables from several sources and coerces them to the declared type.

## Variable definition fields

```yaml
variables:
  project_name:
    type: str
    required: true
    default: demo
    description: Name shown in docs and package metadata
    choices: [demo, sample]
    examples: [demo, sample]
    pattern: "^[a-z0-9-]+$"
    secret: false
```

Supported types:

- `str`
- `int`
- `float`
- `bool`

## Global precedence

For project-level variable resolution, Mixy effectively prefers higher-priority inputs in this
order:

1. variable `default`
2. project `values`
3. environment variables with the `MIXY_VAR_` prefix
4. `--vars-file`
5. CLI `--var`
6. interactive prompt for any still-unresolved required variables

Example:

```yaml
variables:
  project_name:
    type: str
    default: demo-app
    required: false

values:
  project_name: config-name
```

```bash
export MIXY_VAR_PROJECT_NAME=env-name
mixy generate mixy.yml --vars-file vars.yml --var project_name=cli-name
```

If `vars.yml` contains:

```yaml
project_name: vars-file-name
```

The final value is `cli-name`.

## Per-source values

Per-source `values` override the project-level value only when Mixy renders that source. CLI
overrides still win.

```yaml
variables:
  port:
    type: int
    default: 8080
    required: false

values:
  port: 8080

sources:
  - id: api
    values:
      port: 3000
    source:
      type: local_dir
      path: ./templates/api

  - id: docs
    source:
      type: local_dir
      path: ./templates/docs
```

In this example:

- files from `api` see `port=3000`
- files from `docs` see `port=8080`
- `--var port=5000` would override both

## Environment variables

Mixy reads environment variables by uppercasing the variable name and prefixing it with
`MIXY_VAR_`.

Example:

```yaml
variables:
  project_name:
    type: str
```

```bash
export MIXY_VAR_PROJECT_NAME=payments-api
mixy inspect mixy.yml
```

## Vars files

Use `--vars-file` to pass a YAML mapping of variable names to values:

```yaml
# team-values.yml
project_name: payments-api
module_name: payments_api
python_version: "3.13"
```

```bash
mixy generate mixy.yml --vars-file team-values.yml
```

The vars file must contain a top-level YAML mapping.

## CLI overrides

Repeat `--var` for multiple values:

```bash
mixy generate mixy.yml \
  --var project_name=payments-api \
  --var module_name=payments_api
```

Each override must use `KEY=VALUE` format.

## Prompts and non-interactive mode

If a required variable is still unresolved, Mixy prompts for it by default.

```yaml
variables:
  project_name:
    type: str
    description: Name of the generated project
```

Running:

```bash
mixy generate mixy.yml
```

prompts for `project_name`.

Use `--non-interactive` to fail instead of prompting:

```bash
mixy generate mixy.yml --non-interactive
```

Prompting is handled by the application layer. The domain resolver raises a
`VariableResolutionError` when a required variable remains unresolved.

## Type coercion

Mixy coerces string inputs to the declared type.

```yaml
variables:
  retries:
    type: int
  use_docker:
    type: bool
```

```bash
mixy generate mixy.yml --var retries=3 --var use_docker=true
```

This resolves `retries` to `3` and `use_docker` to `True`.

## Choices, patterns, and secrets

Choices:

```yaml
variables:
  python_version:
    type: str
    choices: ["3.11", "3.12", "3.13"]
```

Pattern:

```yaml
variables:
  module_name:
    type: str
    pattern: "^[a-z_]+$"
```

Secret masking:

```yaml
variables:
  db_password:
    type: str
    secret: true
```

Secret values are masked in log output as `***`.
