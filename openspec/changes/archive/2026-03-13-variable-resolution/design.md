## Context

Variable resolution sits between config loading and template rendering. It must merge values from multiple sources into a single, fully-typed, validated dict that the renderer consumes. The precedence order must be intuitive and match user expectations from similar tools (Terraform, Helm, Cookiecutter).

## Goals / Non-Goals

**Goals:**
- Implement deterministic precedence: defaults → env → vars file → per-source overrides → CLI → prompt
- Type coercion from string inputs (env vars, CLI) to declared types
- Constraint validation (choices, regex pattern)
- Interactive prompting with typer prompt for unresolved required vars
- Secret masking in all log output

**Non-Goals:**
- Computed/derived variables
- Variable namespacing per source (flat namespace in MVP)
- Secret vault integrations
- Variable interpolation within other variables

## Decisions

### Precedence chain: prompt is fallback, not override
Prompting happens last but only for values that are still unresolved and required. It does not override explicit values. This matches user expectations: if you passed `--var name=foo`, you shouldn't be prompted for `name`.

### Flat variable namespace with per-source value overrides
Variables are defined globally. The `values` map at project level provides global defaults. Per-source `values` override for that specific source's rendering context. No dot-notation namespacing in MVP.

### Environment variable convention: MIXY_VAR_{UPPER_NAME}
Environment variables are read with prefix `MIXY_VAR_` followed by the uppercase variable name. Example: variable `project_name` reads from `MIXY_VAR_PROJECT_NAME`. This avoids collisions with system env vars.

### Type coercion via Pydantic
Use Pydantic's type coercion for converting string values (from env/CLI) to declared types. This reuses existing infrastructure and handles edge cases (bool parsing, etc.) consistently.

### Secret masking via loguru filter
Register a loguru filter that replaces secret values with `***` in all log output. The filter receives the set of secret values from the resolver.

## Risks / Trade-offs

- [Env var prefix `MIXY_VAR_` is verbose] → Clarity over brevity; avoids accidental collisions
- [Flat namespace may cause variable name collisions across sources] → Acceptable for MVP; namespacing can be added later
- [Interactive prompting blocks CI pipelines] → `--non-interactive` flag causes hard failure on unresolved required vars instead of prompting
