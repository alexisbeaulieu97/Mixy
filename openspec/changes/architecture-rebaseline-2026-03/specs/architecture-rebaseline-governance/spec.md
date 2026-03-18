## ADDED Requirements

### Requirement: Current architecture backlog
The project SHALL maintain a ranked architecture backlog that reflects the current repo state rather than relying on historical planning artifacts alone.

#### Scenario: Rebaselining the program
- **WHEN** completed migration work makes an older architecture plan stale
- **THEN** the architecture program records a new ranked backlog from the current codebase state

### Requirement: One active implementation change at a time
The architecture program SHALL promote exactly one bounded runtime implementation change at a time.

#### Scenario: Selecting the next runtime change
- **WHEN** the team chooses the next architecture refactor
- **THEN** exactly one change is marked active and all later changes remain queued for later re-prioritization

### Requirement: Behavior-preserving migration by default
Architecture refactors SHALL preserve current runtime behavior unless a behavioral contract change is explicitly captured in the change itself.

#### Scenario: Tightening an orchestration boundary
- **WHEN** a change reorganizes application, domain, or infrastructure ownership
- **THEN** existing CLI behavior and generation semantics remain stable unless the change explicitly defines a contract correction
