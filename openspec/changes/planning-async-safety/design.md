## Context

The planning use case is intentionally synchronous because Mixy is a CLI-first tool. However, `_resolve_sources(...)` currently switches to `anyio.run(...)` when multiple sources are present. That makes the public sync use case responsible for event-loop management, which is an awkward boundary and breaks when the function is called while an event loop is already running.

## Goals / Non-Goals

**Goals:**
- Keep `prepare_project(...)` and `plan_project(...)` synchronous
- Remove direct event-loop startup from the use-case surface
- Preserve current multi-source resolution ordering and source-specific error attribution
- Add focused regression tests that prove planning works from an async context

**Non-Goals:**
- Redesigning source providers
- Introducing async public APIs
- Changing CLI options, merge planning semantics, or generation output

## Decisions

### Replace AnyIO task-group orchestration with synchronous thread-based fan-out
Source providers are synchronous today. The simplest safe fix is to use a synchronous thread-based helper for multi-source resolution instead of calling `anyio.run(...)` from a sync use case. This keeps the public API unchanged and avoids nested event-loop problems.

### Preserve deterministic ordering
Parallel source resolution must still return results in the same order as the input source references so merge behavior and error reporting remain stable.

### Keep the fallback path simple
Single-source planning remains on the direct synchronous path. The parallel helper should only be used when there is more than one enabled source reference.

## Implementation Outline

1. Replace the `anyio.run(...)`-based helper in [`mixy/application/use_cases/plan_project.py`](/Users/alexisbeaulieu/Projects/Mixy/mixy/application/use_cases/plan_project.py) with a synchronous concurrency strategy that is safe under a running event loop.
2. Preserve current `SourceResolver.resolve_all([ref])` behavior for each individual reference so source-id remapping and error wrapping stay unchanged.
3. Add a regression test that calls `plan_project(...)` from inside `asyncio.run(...)` and verifies the plan succeeds.
4. Run the focused planning tests and the full suite.

## Risks / Trade-offs

- The change preserves a sync API, so embedded async callers still block while planning runs; this change is about correctness and safety, not async throughput.
- Thread-based fan-out adds a little implementation complexity, but it is smaller and safer than introducing async public APIs.
- If providers later become async-aware, the concurrency strategy may need a different abstraction; that is out of scope here.
