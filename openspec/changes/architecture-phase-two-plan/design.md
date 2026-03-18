## Context

Mixy's architecture is no longer in early bootstrap. The codebase now has working application, domain, and infrastructure seams, a passing test suite, and several completed cleanup changes. The remaining work is narrower: remove the last hard boundary violations, align dead contract surface with runtime behavior, and make application composition explicit.

## Goals / Non-Goals

**Goals:**
- Capture the current architecture state after the first migration wave
- Define the phase-two target architecture and the backlog for getting there
- Keep the migration incremental, behavior-preserving by default, and limited to one active implementation change at a time
- Identify the highest-leverage next change and its validation bar

**Non-Goals:**
- Rewriting Mixy's core generation pipeline
- Reopening already-completed architecture changes unless new evidence requires it
- Bundling multiple implementation refactors into one active change

## Decisions

### Phase two remains incremental
The current codebase does not justify a rewrite. The remaining debt is concentrated in orchestration ownership, public contract drift, and composition seams, so the next wave should continue as bounded refactors.

### `variable-resolution-boundary-extraction` is the active implementation change
The clearest current architecture violation is that the domain `VariableResolver` still owns Typer prompting and global Loguru masking. That change is both high leverage and independently verifiable, so it becomes the next active item.

### The backlog stays ranked and explicit
All follow-up work remains queued behind the active change. The backlog order after this change is:

1. `variable-resolution-boundary-extraction`
2. `source-entry-contract-alignment`
3. `planning-port-and-composition-root`
4. `validate-use-case-consolidation`
5. `openspec-runtime-contract-sync`
6. `planning-async-safety`
7. `execution-atomicity-strategy`

## Target Architecture

```text
Typer CLI
  -> application use cases
     validate_project
     plan_project
     inspect_project
     generate_project
  -> application services / composition
     variable resolution service
     source resolution service
     template rendering service
     dependency assembly
  -> application ports
     ConfigLoader
     VarsFileLoader
     SourceProviderRegistry
     PromptGateway
     TemplateEngine
     GenerationExecutor
  -> domain core
     config models
     variable precedence and validation
     metadata inheritance
     merge planning
     domain exceptions
  -> infrastructure adapters
     YAML loaders
     pluggy-backed source registry
     local/git providers
     Jinja + binary detection
     filesystem execution
     cache and Git client
     logging / secret masking
```

## Migration Sequence

1. Extract variable prompting and log masking out of the domain resolver.
2. Align `TemplateReference` contract surface with actual runtime behavior.
3. Introduce explicit application ports and a composition root for planning/generation.
4. Consolidate `validate` behind an application use case.
5. Repair stale OpenSpec/runtime contract drift in active specs and docs.
6. Decide whether planning should stay sync-only or gain async-safe composition.
7. Address staged writes / atomic execution as an explicit reliability change.

## Risks / Trade-offs

- The queue contains two classes of work: internal boundary cleanup and public contract alignment. Re-prioritization after the active change remains necessary.
- Some stale config surface, such as `merge_strategy`, may require explicit contract removal later rather than silent preservation.
- The meta-change is planning-only; it should not accumulate implementation edits.
