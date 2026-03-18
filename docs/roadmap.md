# Mixy — Implementation Roadmap

## Overview

Mixy is a CLI tool that creates projects from one or more templates. This roadmap breaks the full implementation into 10 changes organized in 5 phases, ordered by dependency. Each change has a complete proposal, design, specs, and task breakdown in `openspec/changes/<name>/`.

To implement any change: `cd` to the project root and run `/opsx:apply <change-name>`.

---

## Phase 1: Foundation

### 1. `project-bootstrap`

> Set up the Python package, dependencies, CLI skeleton, and test infrastructure.

- pyproject.toml with uv, Python >= 3.11
- Dependencies: typer, jinja2, pyyaml, pydantic v2, loguru, platformdirs
- Layered package structure: `mixy/{cli,domain,application,infrastructure}/`
- `mixy version` command
- pytest + ruff + mypy configuration

**Specs:** `cli-entry-point`, `package-structure`
**Depends on:** nothing

---

## Phase 2: Core Domain

### 2. `domain-models-and-config`

> Define the configuration schema, domain models, YAML loading, and validation.

- Pydantic v2 models: ProjectDefinition, TemplateReference, SourceDefinition (discriminated union), VariableDefinition, OutputDefinition
- YAML config loader with version checking
- ConfigValidator domain service (unique IDs, type consistency, path checks)
- Domain exceptions with actionable messages

**Specs:** `config-schema`, `config-validation`
**Depends on:** `project-bootstrap`

### 3. `source-resolution`

> Source provider abstraction and local directory source.

- SourceProvider protocol (can_handle, resolve, fingerprint)
- MaterializedSource value object
- LocalDirProvider implementation
- SourceResolver with provider registry

**Specs:** `source-provider-contract`, `local-dir-source`
**Depends on:** `domain-models-and-config`

### 4. `variable-resolution`

> Variable precedence chain, type coercion, prompting, and secret masking.

- Precedence: defaults → env (`MIXY_VAR_`) → vars file → per-source → CLI → prompt
- Type coercion via Pydantic (str, int, float, bool)
- Constraint validation (choices, pattern)
- Interactive prompting for unresolved required variables
- Secret masking in log output

**Specs:** `variable-resolution`
**Depends on:** `domain-models-and-config`

### 5. `template-rendering-engine`

> Jinja2 rendering for file contents and paths, binary detection.

- Jinja2 with StrictUndefined
- File content and path name rendering
- `.j2` suffix stripping convention
- Binary detection: extension blocklist + null byte heuristic
- Render policy with exclude patterns

**Specs:** `template-rendering`, `binary-detection`
**Depends on:** `domain-models-and-config`

### 6. `merge-planner`

> Deterministic merge planning with conflict detection.

- FileOperation tagged union (CreateDir, CopyRaw, RenderTemplate, SkipExisting, Overwrite)
- Conflict detection across sources
- Conflict policies: fail (default), overwrite, skip
- File-vs-directory conflicts always fail
- RenderPlan output for executor consumption

**Specs:** `merge-planning`
**Depends on:** `source-resolution`, `template-rendering-engine`

---

## Phase 3: End-to-End Pipeline

### 7. `generation-pipeline`

> Orchestrate the full generation flow and file writing.

- `generate_project` use case: load → validate → resolve vars → resolve sources → plan → execute
- GenerationExecutor for filesystem writes
- Dry-run mode (plan display without writes)
- Generation summary with operation counts

**Specs:** `generation-pipeline`, `dry-run-mode`
**Depends on:** `variable-resolution`, `merge-planner`

---

## Phase 4: Git & CLI

### 8. `git-source-and-caching`

> Git repository source provider and local cache store.

- GitClient wrapping the `git` CLI
- Bare clone + extraction strategy
- Cache store using platformdirs (~/.cache/mixy/)
- Cache key: SHA256(url + commit SHA)
- `mixy cache list` and `mixy cache clear` commands

**Specs:** `git-source`, `source-caching`
**Depends on:** `source-resolution`

### 9. `cli-commands-and-ux`

> Full CLI commands, error formatting, and logging.

- `mixy generate` with all options (--output, --var, --vars-file, --dry-run, --non-interactive, --overwrite)
- `mixy validate` — config validation without generation
- `mixy inspect` — show resolved state (variables, sources, merge preview)
- Loguru configuration (stderr, colored, --quiet)
- Error formatting with exit codes (0/1/2)

**Specs:** `cli-generate-command`, `cli-validate-command`, `cli-inspect-command`, `cli-error-formatting`
**Depends on:** `generation-pipeline`, `git-source-and-caching`

---

## Phase 5: Template Metadata

### 10. `recursive-template-metadata`

> Self-describing templates with recursive metadata discovery.

- `.mixy/template.yml` directory-scope metadata
- `<filename>.mixy.yml` file-scope sidecar metadata
- Scope hierarchy: project → source root → nested dirs → file
- Inheritance: scalar (nearest wins), list (union), map (deep merge)
- Variable refinement validation (refine OK, contradict fails)
- Metadata files excluded from output

**Specs:** `template-metadata-discovery`, `metadata-inheritance`
**Depends on:** `generation-pipeline`

---

## Dependency Graph

```
project-bootstrap
  └── domain-models-and-config
        ├── source-resolution
        │     ├── merge-planner ──────────┐
        │     └── git-source-and-caching  │
        ├── variable-resolution           │
        │     └── generation-pipeline ◄───┘
        │           ├── cli-commands-and-ux
        │           └── recursive-template-metadata
        └── template-rendering-engine
              └── merge-planner (also depends on source-resolution)
```

## MVP Scope

The MVP includes all 10 changes. Changes 1-7 form the minimum viable product for local sources. Changes 8-9 add Git support and the full CLI. Change 10 adds template self-description.

## Excluded from MVP

- Hooks / post-processing
- Plugin loading from third-party packages
- Config imports / composition
- Remote archive sources
- Secret vault integrations
- Templating engines beyond Jinja2
- CI/CD pipeline setup
- IDE integrations

## Tech Stack

| Concern | Choice |
|---------|--------|
| Language | Python >= 3.11 |
| Package manager | uv |
| CLI framework | Typer |
| Config parsing | Pydantic v2 + PyYAML |
| Templating | Jinja2 |
| Logging | Loguru |
| Cache paths | platformdirs |
| Testing | pytest + pytest-cov |
| Linting | ruff |
| Type checking | mypy |
