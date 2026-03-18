# Commands

Mixy exposes a small CLI built with Typer.

If you run from a checkout with `uv`, prefix examples with `uv run`.

## Global options

```bash
mixy --help
mixy --log-level debug version
mixy --quiet validate mixy.yml
```

Available global options:

- `--log-level [debug|info|warning|error]`
- `--quiet`

## `mixy version`

Print the installed Mixy version.

```bash
mixy version
```

## `mixy validate`

Validate a config without generating files.

```bash
mixy validate mixy.yml
```

Use this when you want to catch:

- schema errors
- duplicate source ids
- variable default and choice type mismatches
- warnings for missing local paths

## `mixy inspect`

Inspect resolved variables, sources, and the merge preview.

```bash
mixy inspect mixy.yml
```

Useful options:

```bash
mixy inspect mixy.yml \
  --vars-file team-values.yml \
  --var project_name=payments-api \
  --output ./preview
```

What `inspect` shows:

- config summary
- resolved variable table with value source
- source table
- merge preview table

## `mixy generate`

Generate files from a config.

```bash
mixy generate mixy.yml
```

Common examples:

Generate with overrides:

```bash
mixy generate mixy.yml \
  --var project_name=payments-api \
  --var module_name=payments_api
```

Generate with a vars file:

```bash
mixy generate mixy.yml --vars-file team-values.yml
```

Override the output path:

```bash
mixy generate mixy.yml --output ./tmp/out
```

Preview without writing files:

```bash
mixy generate mixy.yml --dry-run
```

Fail instead of prompting:

```bash
mixy generate mixy.yml --non-interactive
```

Force overwrite behavior:

```bash
mixy generate mixy.yml --overwrite
```

Options:

- `--output PATH`: override `output.path`
- `--var KEY=VALUE`: repeatable variable override
- `--vars-file PATH`: load YAML values from a file
- `--non-interactive`: fail on unresolved required variables
- `--dry-run`: print the planned actions without writing files
- `--overwrite`: force overwrite conflict handling for this run

## `mixy cache list`

List cached Git worktrees.

```bash
mixy cache list
```

Output columns:

- URL
- REF
- SHA
- SIZE

## `mixy cache clear`

Clear the entire cache:

```bash
mixy cache clear
```

Clear only one repository:

```bash
mixy cache clear --url https://github.com/example/templates.git
```

## Exit behavior

- `0`: success
- `1`: user-facing validation or resolution error
- `2`: system-level or unexpected error
