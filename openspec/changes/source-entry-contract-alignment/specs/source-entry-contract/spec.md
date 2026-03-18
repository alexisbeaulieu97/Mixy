## ADDED Requirements

### Requirement: Template reference contract stays aligned with runtime
The system SHALL expose only source-entry fields whose behavior is explicitly supported and implemented.

#### Scenario: Disabled sources are skipped
- **WHEN** a source entry sets `enabled: false`
- **THEN** the source is not resolved, merged, or generated

#### Scenario: Alias remains metadata only
- **WHEN** a source entry sets `alias`
- **THEN** the alias is carried into source metadata only
- **AND** planning behavior does not change because of the alias

#### Scenario: Unsupported merge strategy is rejected
- **WHEN** a source entry sets `merge_strategy`
- **THEN** configuration loading or planning fails with a clear unsupported-field error

#### Scenario: Reference-level git subpath is rejected
- **WHEN** a git source entry sets `TemplateReference.subpath`
- **THEN** configuration loading or planning fails with a clear error explaining that git subpaths must use `source.subpath`
