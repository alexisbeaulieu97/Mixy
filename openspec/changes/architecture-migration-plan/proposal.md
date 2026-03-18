## Why

Mixy's current structure is directionally sound, but orchestration logic and ownership boundaries have already started to drift. The project needs a documented migration program so refactors stay incremental, preserve behavior, and are executed one bounded change at a time.

## What Changes

- Create a planning-only architecture migration change that documents the current state, target architecture, and phased migration path
- Define prioritization rules for bounded refactors, including one active implementation change at a time
- Record the ranked backlog of candidate implementation changes and the dependencies between them
- Document constraints, non-goals, risks, and unknowns so future changes do not expand scope implicitly

## Capabilities

### New Capabilities
- `architecture-migration-governance`: Governs how architecture refactors are scoped, prioritized, and sequenced through OpenSpec changes

### Modified Capabilities

## Impact

- Adds planning artifacts under `openspec/changes/architecture-migration-plan/`
- Establishes the migration contract for future implementation changes such as shared planning, source contract alignment, and boundary cleanup
- Does not change runtime behavior, public CLI commands, or package APIs
