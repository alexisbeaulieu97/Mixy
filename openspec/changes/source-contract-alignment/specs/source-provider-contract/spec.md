## MODIFIED Requirements

### Requirement: SourceProvider protocol
The system SHALL define a SourceProvider protocol with three methods: `can_handle(source: SourceDefinition) -> bool`, `resolve(source: SourceDefinition) -> MaterializedSource`, and `fingerprint(source: SourceDefinition) -> str`.

#### Scenario: Provider dispatching
- **WHEN** SourceResolver receives a source definition
- **THEN** it iterates registered providers and delegates to the first whose `can_handle` returns True

#### Scenario: No matching provider
- **WHEN** no registered provider can handle a source definition
- **THEN** the system raises a `SourceResolutionError` identifying the unsupported source type and naming `local_dir` and `git` as the supported source types
