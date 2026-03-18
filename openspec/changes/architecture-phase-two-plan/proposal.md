## Why

The first migration wave stabilized Mixy's package boundaries, but the resulting architecture program is now historical context rather than the current source of truth. The repo needs a phase-two planning change that captures the actual remaining debt, the updated target architecture, and the ranked backlog that should drive the next bounded refactors.

## What Changes

- Create a planning-only phase-two architecture change that documents the current repo state after the first migration wave
- Record the updated target architecture, migration principles, and decision that only one bounded implementation change is active at a time
- Capture the ranked backlog for the next set of architecture changes, including dependencies, risks, and validation expectations
- Promote `variable-resolution-boundary-extraction` as the next implementation change

## Capabilities

### New Capabilities
- `architecture-phase-two-governance`: Governs the second migration wave, including backlog ranking, active-change selection, and re-prioritization

### Modified Capabilities
- `architecture-migration-governance`: Superseded by the phase-two plan as the current architecture-program record

## Impact

- Adds planning artifacts under `openspec/changes/architecture-phase-two-plan/`
- Establishes the current backlog for phase-two architecture work
- Does not change runtime behavior, CLI contracts, or package APIs
