## ADDED Requirements

### Requirement: Execution failure guarantees are explicit
The system SHALL define and document its behavior when filesystem execution fails after output mutation has started.

#### Scenario: Mid-execution write failure
- **WHEN** a filesystem write fails during generation
- **THEN** generation stops at the first failing operation
- **AND** any files or directories written before the failure remain on disk
- **AND** the system does not guarantee rollback or cleanup of partial output
- **AND** the failure result identifies the failed operation and target path
