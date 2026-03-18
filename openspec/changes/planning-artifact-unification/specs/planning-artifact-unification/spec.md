## ADDED Requirements

### Requirement: Pre-merge planning artifact is collected once
The system SHALL collect the file-entry and directory-ownership inputs for merge planning once during planning rather than rediscovering the source tree inside merge planning.

#### Scenario: Planning a project with multiple sources
- **WHEN** the system prepares the data needed for merge planning
- **THEN** the pre-merge artifact is built once from the planned sources and render decisions
- **AND** merge planning consumes that artifact directly

### Requirement: Unified artifact preserves merge behavior
The system SHALL preserve current source ordering, conflict detection, and output operation behavior after unifying the planning artifact.

#### Scenario: Preserving merge semantics
- **WHEN** the system plans operations for multiple sources
- **THEN** file conflicts, file-vs-directory conflicts, and overwrite/skip behavior match the previous semantics
