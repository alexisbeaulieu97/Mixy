## ADDED Requirements

### Requirement: Secondary docs match the runtime contract
The system SHALL keep secondary documentation aligned with the current runtime contract when those docs describe supported behavior in the present tense.

#### Scenario: Correcting stale PRD contract text
- **WHEN** a secondary document describes unsupported fields or source kinds as current behavior
- **THEN** that document is updated to match the implemented runtime

### Requirement: Docs-only alignment does not change runtime behavior
The system SHALL treat runtime-contract doc rebaselining as a documentation-only change.

#### Scenario: Rebaselining product docs
- **WHEN** the team aligns secondary docs with the current runtime
- **THEN** no runtime code or CLI behavior changes as part of that change
