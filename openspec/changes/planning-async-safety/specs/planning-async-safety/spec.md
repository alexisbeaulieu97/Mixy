## ADDED Requirements

### Requirement: Sync planning is safe from async contexts
The system SHALL allow `plan_project(...)` and `prepare_project(...)` to be called from code running under an existing event loop without failing due to nested event-loop startup.

#### Scenario: Planning from a running event loop
- **WHEN** application code calls `plan_project(...)` while an event loop is already running
- **THEN** planning completes without attempting to start a nested event loop

### Requirement: Multi-source planning preserves ordering
The system SHALL preserve source-reference ordering when resolving multiple sources concurrently inside sync planning.

#### Scenario: Resolving multiple sources
- **WHEN** planning resolves more than one enabled source reference
- **THEN** the resolved source list preserves the same order as the input references
- **AND** downstream merge behavior remains unchanged
