## Why

The architecture migration program has advanced beyond the last planning artifacts. The codebase now includes the first migration wave, the phase-two cleanup wave, and the follow-on bounded changes that were previously only planned. That makes the current architecture tracker stale: it still describes already-completed work as queued backlog. The repo needs a new planning-only rebaseline that treats the current tree as source of truth and records the remaining migration work from here.

## What Changes

- Create a planning-only architecture rebaseline change that summarizes the current repo state after the completed migration waves
- Record the current target architecture, migration strategy, constraints, risks, and unknowns
- Replace the outdated ranked backlog with a current backlog of remaining bounded changes
- Preserve the one-active-change rule and promote `planning-async-safety` as the next runtime implementation change

## Capabilities

### New Capabilities
- `architecture-rebaseline-governance`: Governs the post-phase-two architecture backlog, active-change selection, and re-prioritization from the current repo state

### Modified Capabilities
- `architecture-phase-two-governance`: Superseded as the current architecture-program tracker by this rebaseline

## Impact

- Adds planning artifacts under `openspec/changes/architecture-rebaseline-2026-03/`
- Establishes the current architecture backlog and active runtime change without altering runtime behavior
- Does not change CLI commands, config schema, package APIs, or generation semantics
