# Mixy — Architecture & Design Draft

## 1. Purpose

Mixy is a CLI tool that creates a project from one or more templates. Templates currently come from local directories or Git repositories. They may contain variables that are resolved at runtime, and the resulting rendered content is merged into a single output project directory.

This document defines the high-level architecture, core domain model, major design decisions, and implementation boundaries so an agent can later decompose the work into tasks and subtasks.

## 2. Goals

* Create reproducible projects from reusable configuration.
* Support multiple template source types through a clean extension model.
* Render templates with variables supplied at runtime.
* Merge multiple templates into one destination directory deterministically.
* Keep the CLI ergonomic and predictable.
* Make the codebase testable, modular, and easy to extend.

## 3. Non-Goals

* Full package manager behavior.
* Arbitrary remote code execution.
* Complex workflow orchestration beyond project generation.
* IDE/editor integrations in the first version.

## 4. Core Use Cases

### 4.1 Generate a project from a config file

A user runs a command with a project config. Mixy resolves sources, prompts or reads variables, renders templates, merges files, and writes the output project.

### 4.2 Generate from multiple sources

A user combines several templates, for example a Python base template, a CI template, and a Docker template, into one final project.

### 4.3 Reuse the same config with different runtime values

A team stores a reusable Mixy config in version control and generates several projects by changing only variable values.

### 4.4 Inspect and validate before generation

A user validates the config and previews what would happen before writing files.

## 5. Key Open Design Questions

1. What is the exact config schema and versioning strategy?
2. How are variables declared, typed, validated, defaulted, and prompted?
3. What is the merge policy when two templates produce the same path?
4. What files are rendered through Jinja and what files are copied raw?
5. What is the trust model for remote templates, especially Git repositories?
6. What is cached locally, where, and how is cache invalidated?
7. What is the extension mechanism for new source types?
8. What is the error model and rollback behavior if generation fails midway?
9. What is the boundary between domain logic and CLI/application orchestration?
10. How much of DDD is genuinely useful here versus ceremonial architecture cosplay?

## 6. Architectural Style

Mixy should use a layered architecture with explicit boundaries:

* **Domain layer**: pure business concepts and rules.
* **Application layer**: use cases and orchestration.
* **Infrastructure layer**: filesystem, Git access, HTTP, YAML loading, caching, templating engine integration.
* **Interface layer**: Typer CLI commands and user interaction.

DDD is useful here mainly for:

* a clear ubiquitous language,
* isolating domain rules from tool/framework concerns,
* keeping source resolution / rendering / merge logic from becoming tangled.

DDD should remain lightweight. This is a CLI generator, not a small religion.

## 7. Proposed Domain Model

### 7.1 Entities / Value Objects

#### ProjectDefinition

Represents the parsed configuration file.

Possible fields:

* `name: str | None`
* `version: str`
* `description: str | None`
* `sources: list[TemplateReference]`
* `variables: dict[str, VariableDefinition]`
* `output: OutputDefinition | None`
* `hooks: HooksDefinition | None` (optional, likely not MVP)

#### TemplateReference

Represents one template input in ordered sequence.

Possible fields:

* `id: str`
* `source: SourceDefinition`
* `subpath: str | None`
* `alias: str | None`
* `enabled: bool = True`
* `values: dict[str, Any] = {}`
* `merge_strategy: unsupported and rejected by config validation`
* `render: RenderPolicy | None`

#### SourceDefinition

Abstract concept for where template content comes from.
Concrete kinds currently supported:

* `local_dir`
* `git`

Future kinds may include:

* remote archive
* package/plugin source

#### VariableDefinition

Represents a variable contract.

Possible fields:

* `name: str`
* `type: VariableType`
* `required: bool`
* `default: Any | None`
* `description: str | None`
* `choices: list[Any] | None`
* `pattern: str | None`
* `secret: bool = False`

#### RenderPlan

Represents the fully resolved generation plan before execution.
Contains:

* resolved sources
* effective variable values
* ordered file operations
* conflicts
* output path

#### FileOperation

Represents a planned action.
Examples:

* create directory
* copy raw file
* render templated file
* skip existing file
* overwrite file
* fail on conflict

#### Conflict

Represents a path collision or incompatible operation.

### 7.2 Domain Services

#### SourceResolver

Turns a `SourceDefinition` into a local materialized source tree.

#### VariableResolver

Combines defaults, config overrides, CLI overrides, environment values, and prompts into final typed values.

#### TemplateRenderer

Determines whether content/path should be rendered and performs Jinja rendering.

#### MergePlanner

Builds the deterministic file operation plan from ordered sources and merge rules.

#### GenerationExecutor

Executes the plan against the filesystem.

#### ConfigValidator

Validates project definition semantics beyond schema validation.

## 8. Application Layer Use Cases

### 8.1 `generate_project`

Inputs:

* config path
* output path override
* variable overrides
* non-interactive flag
* dry-run flag

Flow:

1. Load config.
2. Validate schema and semantics.
3. Resolve variables.
4. Resolve/materialize sources.
5. Build merge plan.
6. Show preview if requested.
7. Execute file operations.
8. Emit summary.

### 8.2 `validate_project_definition`

Loads and validates config without generating files.

### 8.3 `inspect_project_definition`

Shows resolved variables, source order, merge strategy, and expected outputs.

### 8.4 `list_cache` / `clear_cache`

Manages cached source material.

## 9. CLI Surface Proposal

Potential commands:

* `mixy generate CONFIG_PATH`
* `mixy validate CONFIG_PATH`
* `mixy inspect CONFIG_PATH`
* `mixy cache list`
* `mixy cache clear`
* `mixy version`

Potential options:

* `--output PATH`
* `--var KEY=VALUE` (repeatable)
* `--vars-file PATH`
* `--non-interactive`
* `--dry-run`
* `--overwrite`
* `--log-level`

## 10. Configuration Design (Draft)

Mixy should separate **project composition config** from **template-local metadata**.

* **Project composition config** defines which sources are included, how they are combined, output behavior, and runtime-supplied values.
* **Template-local metadata** lives beside template content and defines variables, render rules, include/exclude behavior, and other content-local semantics.

This means Mixy uses **recursive metadata discovery** within each materialized source tree.

### 10.1 Metadata Containers

#### Directory / repository scope

A directory or repository may contain:

```text
.mixy/
  template.yml
```

This metadata applies to that directory subtree.

#### File scope

An individual file may contain adjacent sidecar metadata:

```text
<filename>.mixy.yml
```

Examples:

* `Dockerfile.mixy.yml`
* `main.py.j2.mixy.yml`
* `README.md.mixy.yml`

This metadata applies only to that file.

### 10.2 Scope Hierarchy

Metadata is resolved by specificity:

1. project-level defaults
2. source root scope
3. nested directory scopes
4. file scope

More specific scopes override or refine less specific scopes according to field-specific rules.

### 10.3 Important Boundary

Recursive metadata governs **content-local behavior within a source tree**. It does **not** govern how sources are fetched or how multiple sources are combined.

Therefore the following remain outside recursive metadata:

* source locator (`path`, `url`, `ref`)
* output path
* cross-source merge order
* cache policy
* CLI behavior
* global generation mode

### 10.4 Project Config Shape

Use a nested `source:` object for source-provider-specific configuration.

```yaml
version: "1"
name: flask-app

sources:
  - id: base
    source:
      type: git
      url: https://github.com/example/python-base-template.git
      ref: main
      subpath: template

  - id: ci
    source:
      type: local_dir
      path: ./templates/ci

values:
  project_name: my_app
  python_version: "3.12"

output:
  path: ./out
  conflict_policy: fail
```

### 10.5 Directory Metadata Example

```yaml
name: python-base
version: "1"

variables:
  project_name:
    type: str
    required: true
    description: Python package name

  python_version:
    type: str
    default: "3.12"

render:
  path_names: true
  text_files: true
  exclude:
    - "*.png"
    - "*.jpg"
```

### 10.6 File Sidecar Example

```yaml
variables:
  base_image:
    type: str
    default: python:3.12-slim

render:
  text: true
  path_name: false
```

### 10.7 Full-App Recommendation

Support recursive metadata discovery across directory and file scopes in the main design, not just as a future afterthought. However, keep the inheritance rules strict and narrow so the model remains predictable.

## 10A. Recursive Metadata Rules

```yaml
version: "1"
name: flask-app
sources:
  - id: base
    type: git
    url: https://github.com/example/python-base-template.git
    ref: main
    subpath: template

  - id: ci
    type: git
    url: https://github.com/example/github-actions-template.git
    ref: v1.2.0

variables:
  project_name:
    type: str
    required: true
    description: Project package name

  python_version:
    type: str
    default: "3.12"
    choices: ["3.10", "3.11", "3.12"]

output:
  path: ./out
  conflict_policy: fail
```

Open questions:

* Should source-specific fields live inline or under `source:`?
* Should `variables` support nested objects?
* Should configs support composition/imports?
* How should config schema evolve over versions?

## 10A. Recursive Metadata Rules

### 10A.1 Discovery

For each materialized source tree:

1. discover source root metadata from `.mixy/template.yml` if present
2. walk nested directories and collect additional `.mixy/template.yml` files
3. discover file sidecars matching `<filename>.mixy.yml`
4. build effective metadata for each file/directory from inherited scopes

### 10A.2 What May Appear in Recursive Metadata

Recommended allowed fields for directory/file scope:

* `variables`
* `defaults`
* `render`
* `include`
* `exclude`
* `copy_mode` (`render` / `raw`)
* `notes` or `description`
* optional future `conditions`

Recommended disallowed fields in recursive metadata:

* `source`
* `output`
* `cache`
* cross-source `merge_strategy`
* `hooks` that execute commands
* `imports` of additional sources (at least until explicitly designed)

### 10A.3 Inheritance Rules

#### Behavioral settings

For behavior-oriented fields such as `render`, `include`, `exclude`, or `copy_mode`, the nearest scope wins unless the field is explicitly mergeable.

Suggested rule set:

* scalar settings: nearest scope overrides
* list settings such as `exclude`: inherited union, unless explicitly marked replace
* maps such as `render`: deep merge by key with child override

#### Variable definitions

Nested scopes may **refine** but not **contradict** parent definitions.

Allowed refinements may include:

* adding description/help text
* providing a more specific default
* adding compatible examples or metadata

Forbidden contradictions include:

* changing variable type
* changing `secret` semantics incompatibly
* introducing incompatible constraints or choices

If two scopes define the same variable incompatibly, Mixy fails during planning with an explicit compatibility error.

### 10A.4 Composition Boundary

Recursive metadata discovery is about **local scope resolution inside a source tree**. It is not recursive template inclusion. A template does not implicitly import other templates unless Mixy later gains an explicitly designed dependency system.

## 11. Variable Resolution Strategy

Proposed precedence, lowest to highest:

1. variable default from config
2. environment values
3. vars file
4. per-source variable overrides
5. CLI `--var`
6. interactive prompt

This needs a decision because prompting last is unusual if required values are still missing. A better model may be:

1. defaults
2. environment
3. vars file
4. CLI overrides
5. prompt for unresolved required values

Questions:

* Should per-source variables shadow global variables or be namespaced?
* Do we support computed variables?
* How are secrets handled in prompts and logs?

## 12. Rendering Rules

This is a major design seam.

Questions to settle:

* Are both file contents and file/directory names rendered?
* Which files are treated as templates?
* Do we use suffix-based rendering like `.j2`, allowlists, blocklists, or “render everything as text unless binary”?
* How do we detect binary files safely?

Proposed MVP:

* Render file contents for text files only.
* Render file and directory names.
* Use strict undefined variables.
* Allow opt-out patterns for raw copy.
* Detect binary files and never render them.

## 13. Merge Semantics

This is the most important behavioral contract.

Questions:

* Does later source always win?
* Are directories merged recursively?
* What happens when file vs directory conflicts occur?
* Is conflict policy global, per-source, or per-path?

Proposed baseline:

* Sources are applied in declared order.
* Directories merge recursively.
* If two files target the same path:

  * `fail` by default
  * optional `overwrite`, where later source wins
  * optional `skip`, where earlier source wins
* File vs directory conflicts always fail.

## 14. Source Types and Infrastructure Strategy

### 14.1 Local file / directory

Simple filesystem-backed source.

### 14.2 Git repository

Needs clone/fetch/materialize strategy.

Open questions:

* Shell out to git or implement via Python library?
* Is `git` executable required on the host?
* Do we support auth for private repositories in MVP?
* Do we cache cloned repositories by URL + ref?

Pragmatic suggestion:

* Shell out to `git` for MVP.
* Fail clearly if git is unavailable.
* Cache repositories under platformdirs cache dir.

### 14.3 Future remote sources

Remote archive or HTTP-hosted template packs could be added later through the same source provider abstraction.

## 15. Caching

Use `platformdirs` for cache paths.

Cache candidates:

* cloned repositories
* downloaded remote artifacts
* maybe parsed metadata if worthwhile

Questions:

* What is the cache key format?
* Do we pin a Git ref to commit SHA after fetch?
* How does offline mode behave?

Suggested cache key:

* source type
* canonical source locator
* requested ref
* resolved commit SHA if applicable

## 16. Error Handling and Safety

Desired properties:

* deterministic failures
* no silent overwrites unless explicitly configured
* actionable error messages
* support dry-run preview

Questions:

* Do we write into a temp directory and then move into place?
* Do we support rollback?
* What happens if partial writes already occurred?

Suggested MVP:

* Plan first, fail before writes if any conflict exists.
* Execute writes after plan approval.
* Consider staging in temp dir only if atomicity becomes important.

## 17. Logging and UX

Use `loguru` for structured, readable CLI logs.

Need to define:

* user-facing console messages vs debug logs
* progress reporting for source fetching and rendering
* summary output after generation
* quiet/non-interactive behavior

## 18. Package Structure Proposal

```text
mixy/
  cli/
    app.py
    commands/
      generate.py
      validate.py
      inspect.py
      cache.py
  application/
    use_cases/
      generate_project.py
      validate_project_definition.py
      inspect_project_definition.py
    dto/
    services/
  domain/
    models/
      project_definition.py
      template_reference.py
      variables.py
      render_plan.py
      file_operation.py
      conflicts.py
    services/
      source_resolver.py
      variable_resolver.py
      merge_planner.py
      template_renderer.py
      config_validator.py
    enums/
    exceptions/
  infrastructure/
    config/
      yaml_loader.py
      settings.py
    filesystem/
      file_writer.py
      tempdirs.py
    sources/
      base.py
      local.py
      git.py
    rendering/
      jinja_renderer.py
      binary_detection.py
    cache/
      cache_store.py
    process/
      git_client.py
    logging/
      logger.py
  tests/
    unit/
    integration/
    fixtures/
```

## 19. Extension Model

A useful abstraction is a `SourceProvider` interface.

Candidate interface:

* `can_handle(source_definition) -> bool`
* `resolve(source_definition, context) -> MaterializedSource`
* `fingerprint(source_definition) -> str`

Possibly also a render policy abstraction later.

Questions:

* Do we need plugin discovery in MVP, or just internal provider registry?
* Should new providers be code plugins or config-driven only?

Recommendation:

* Internal provider registry in MVP.
* Design interfaces so plugin loading can be added later.

## 20. Testing Strategy

TDD is appropriate here if we are disciplined about the seams.

Test layers:

### Unit tests

* config validation
* variable precedence and typing
* merge planner behavior
* render decisions
* path conflict detection

### Integration tests

* generate from local sources
* generate from Git source
* dry-run output
* cache behavior
* CLI behavior via Typer runner

### Contract tests

* each source provider obeys the same materialization contract

Important test matrix:

* file/file conflict
* file/directory conflict
* binary vs text render
* missing variable
* strict undefined Jinja
* repeated generation into non-empty output

## 21. Recommended Early Decisions

These should be settled before task breakdown:

1. Config schema shape and version field.
2. Exact merge/conflict policy.
3. Variable precedence and prompt behavior.
4. Rendering scope and binary detection rules.
5. Git strategy and cache behavior.
6. MVP source types.
7. Whether hooks/post-processing exist in MVP.

## 22. Suggested MVP Scope

Keep MVP narrow:

* YAML config
* local directory source
* Git repository source
* global variables with simple types
* Jinja rendering for paths + text files
* deterministic merge planning
* dry-run + validate
* caching for Git repos

Exclude from MVP:

* hooks
* plugin loading from third-party packages
* config imports
* remote archives
* secret vault integrations
* templating beyond Jinja2

## 23. Risks

### Risk: merge behavior becomes surprising

Mitigation: explicit conflict policy, dry-run, inspect command.

### Risk: rendering corrupts binary files

Mitigation: strong binary detection, raw copy default for binaries.

### Risk: Git source handling becomes flaky

Mitigation: shell out to git, integration tests, cache isolation.

### Risk: overengineering with DDD

Mitigation: keep domain model focused on real rules, not decorative abstraction.

## 24. Decisions Log

### Accepted

* None yet.

### Rejected

* None yet.

## 25. Next Discussion Targets

1. Finalize config schema.
2. Finalize merge semantics.
3. Finalize variable model and precedence.
4. Define source provider contract.
5. Decide MVP vs post-MVP boundaries.
