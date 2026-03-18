## Context

Mixy already has a layered package layout, but the highest-risk debt is concentrated in orchestration seams rather than in the core domain model. The migration should therefore focus on making existing boundaries real, not on replacing the current product with a new design.

## Goals / Non-Goals

**Goals:**
- Define the target architecture and the migration sequence from the current state
- Keep behavior stable unless a current contract mismatch is explicitly corrected
- Ensure each implementation change is bounded, independently testable, and reviewable
- Keep exactly one implementation change active at a time and re-rank the backlog after completion

**Non-Goals:**
- Rewriting the CLI, domain model, merge planner, or metadata system
- Introducing speculative new extension points without an immediate consumer
- Bundling multiple unrelated refactors into one OpenSpec change

## Decisions

### Migration follows a meta-change plus one active implementation change
This change is planning-only. It creates the architecture program and ranked backlog, but only one implementation change is promoted at a time. That keeps work reviewable and prevents overlapping refactors from obscuring regressions.

### The first implementation target is the shared planning seam
The highest-leverage issue is duplicated pre-execution orchestration between `generate` and `inspect`. The first implementation change will extract a shared application planning use case and migrate both commands onto it before broader boundary cleanup begins.

### Refactor around seams, not broad rewrites
The current domain rules for variable resolution, metadata inheritance, merge planning, and rendering are already covered by tests. Migration should wrap and reorganize these components behind clearer application seams before considering deeper decomposition.

## Target Architecture

```text
Typer CLI
  -> application use cases
     validate_project
     plan_project
     inspect_project
     generate_project
  -> application ports
     ConfigLoader
     SourceProviderRegistry
     TemplateEngine
     PromptGateway
     GenerationExecutor
  -> domain core
     config/models
     variable precedence + validation rules
     metadata inheritance rules
     merge planner
     domain exceptions
  -> infrastructure adapters
     YAML loaders
     local/git providers
     pluggy registry
     Jinja renderer + binary detection
     filesystem executor
     logging
```

## Migration Sequence

1. Introduce a shared project planning use case and move `inspect` and `generate` onto it.
2. Align source-provider contracts so schema, validation, runtime, and docs agree.
3. Decompose render planning into smaller collaborators behind the shared planning seam.
4. Move impure provider and renderer contracts behind application ports.
5. Harden Git integration, error handling, and low-coverage failure paths.
6. Add lightweight boundary enforcement only after the major seams are stable.

## Risks / Trade-offs

- The worktree is already dirty in several orchestration files, so changes must be merged carefully rather than assuming pristine history.
- The meta-change requires a spec artifact even though it is planning-only; that spec should be treated as governance documentation, not runtime behavior.
- Backlog ordering may change after each implementation change reveals new coupling or reduces uncertainty.
