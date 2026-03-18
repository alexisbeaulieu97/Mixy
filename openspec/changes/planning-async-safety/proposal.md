## Why

`plan_project(...)` is a synchronous public use case, but it currently starts an event loop internally with `anyio.run(...)` when resolving multiple sources. That is safe for the CLI, but it fails or becomes awkward when Mixy is invoked from an already-running event loop. This is the clearest remaining runtime architecture risk in the planning seam and it can be corrected without changing CLI semantics.

## What Changes

- Remove or isolate direct event-loop bootstrapping from the sync planning use-case surface
- Keep `plan_project(...)` and `prepare_project(...)` publicly synchronous
- Preserve source-resolution ordering and existing error behavior while making multi-source planning safe from async contexts
- Add focused regression tests for planning from both normal sync code and from a running event loop

## Capabilities

### New Capabilities
- `planning-async-safety`: Sync-safe project planning that does not require starting an event loop inside the public use case

## Impact

- Refactors internal planning orchestration only
- Preserves CLI behavior, config schema, and generation semantics
- Adds regression coverage around async-context invocation
