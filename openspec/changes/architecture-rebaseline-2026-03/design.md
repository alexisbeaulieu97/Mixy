## Context

Mixy's architecture is no longer in the middle of the first migration wave. The repo now has a shared planning seam, application-owned orchestration services, a composition root, validation use-case consolidation, source-entry contract alignment, runtime/spec sync, boundary guardrails, and execution/reporting hardening. The strongest remaining debt is narrower and more local:

- the current architecture program tracker is stale
- `plan_project.py` remains the main orchestration hotspot
- the application layer still imports several infrastructure defaults directly
- sync planning still starts an event loop internally via `anyio.run(...)`
- planning and merge planning still duplicate some filesystem discovery work
- some secondary docs remain ahead of or behind runtime reality

## Goals / Non-Goals

**Goals:**
- Rebaseline the architecture program against the current codebase instead of historical backlog artifacts
- Record the current target architecture and the remaining bounded refactors
- Keep exactly one runtime implementation change active at a time
- Preserve runtime behavior by default unless a later change explicitly captures a contract correction

**Non-Goals:**
- Reopening completed changes unless new evidence requires it
- Rewriting Mixy's CLI, domain model, merge planner, metadata rules, or source providers
- Turning the rebaseline itself into a runtime refactor

## Decisions

### Treat earlier architecture plans as historical, not current backlog
`architecture-migration-plan` and `architecture-phase-two-plan` remain valuable historical records, but they no longer represent the current backlog. This change becomes the current architecture-program tracker.

### Promote exactly one active runtime change
`planning-async-safety` is the next active implementation change. It is bounded, low ambiguity, and independently verifiable. All other remaining work stays queued until it is re-prioritized after that change completes.

### Continue with incremental migration, not rewrite
The repo does not justify a rewrite. The domain core is stable and well tested. The remaining work is mainly about tightening orchestration boundaries, removing the last coupling seams, and keeping the documentation truthful.

### Keep future queued changes as backlog items until promoted
The rebaseline records the next ranked changes, but only `planning-async-safety` should be implemented immediately. `planning-infrastructure-port-completion`, `planning-artifact-unification`, `renderer-boundary-finalization`, and `runtime-contract-doc-rebaseline` remain queued.

## Current-State Summary

```text
Typer CLI
  -> application use cases
     validate_project
     plan_project
     inspect command formatting
     generate_project
  -> application services / composition
     variable resolution service
     source resolution service
     template rendering service
     dependency assembly
  -> domain core
     config models
     variable precedence + validation rules
     metadata inheritance rules
     merge planning
     domain exceptions
  -> infrastructure adapters
     YAML loaders
     metadata loader
     local/git providers
     pluggy registry
     prompt adapter
     Jinja + binary detection
     filesystem executor
     cache, git client, logging
```

The core architectural diagnosis is:

- the repo is directionally sound and not a rewrite candidate
- orchestration ownership is mostly correct but still incomplete
- the main residual design debt is concentrated in planning, composition, and documentation drift

## Target Architecture

```text
Typer CLI
  -> application use cases
     validate_project
     plan_project
     generate_project
     inspect formatting / presentation
  -> application coordinators and ports
     config loader
     vars file loader
     metadata discovery
     source provider registry
     prompt gateway
     secret masking strategy
     rendering engine
     generation executor
  -> domain core
     config models
     variable rules
     metadata rules
     merge planning
     domain exceptions
  -> infrastructure adapters
     YAML and vars loaders
     metadata loader
     local/git providers
     pluggy-backed provider registry
     Typer prompt adapter
     Loguru masking / logging
     Jinja rendering helpers
     filesystem execution
```

## Ranked Backlog

1. `planning-async-safety`
   - Goal: keep planning publicly sync while removing direct event-loop bootstrapping from the use-case surface
   - Why: it is the clearest unresolved runtime risk, especially for embedded callers
   - Validation: focused regression tests for sync use and running-event-loop use, then full suite
2. `planning-infrastructure-port-completion`
   - Goal: move the remaining application-level infrastructure defaults behind minimal application-owned interfaces and composition
   - Validation: composition tests, use-case tests, full suite
3. `planning-artifact-unification`
   - Goal: reuse one planned-entry artifact across planning and merge planning instead of rediscovering source trees
   - Validation: planning/generation regression tests and fixture comparisons
4. `renderer-boundary-finalization`
   - Goal: clarify whether rendering policy lives in the application layer or behind a rendering adapter without changing behavior
   - Validation: renderer/planning/metadata tests and full suite
5. `runtime-contract-doc-rebaseline`
   - Goal: align PRD and secondary docs with actual supported runtime behavior
   - Validation: targeted doc/spec audit

## Migration Strategy

1. Record the current architecture state and backlog in this planning-only change.
2. Implement `planning-async-safety` as the only active runtime change.
3. Re-rank the remaining backlog after that change completes.
4. Continue executing one bounded change at a time, preserving behavior unless a change explicitly states otherwise.

## Risks / Trade-offs

- The async-planning risk matters more to embedded/library callers than to current CLI users.
- Some docs, especially the product PRD, may be intentionally aspirational. The authoritative docs/specs should be aligned first if the distinction matters.
- The worktree is already dirty, so this rebaseline must treat the current tree as truth rather than assuming prior plans remain current.
- Backlog ordering may still shift after `planning-async-safety` reduces uncertainty around the planning seam.
