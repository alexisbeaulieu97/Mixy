## ADDED Requirements

### Requirement: SourceProvider protocol
The system SHALL define a SourceProvider protocol with three methods: `can_handle(source: SourceDefinition) -> bool`, `resolve(source: SourceDefinition) -> MaterializedSource`, and `fingerprint(source: SourceDefinition) -> str`.

#### Scenario: Provider dispatching
- **WHEN** SourceResolver receives a source definition
- **THEN** it iterates registered providers and delegates to the first whose `can_handle` returns True

#### Scenario: No matching provider
- **WHEN** no registered provider can handle a source definition
- **THEN** the system raises a `SourceResolutionError` identifying the unsupported source type

### Requirement: MaterializedSource value object
The system SHALL represent a resolved source as a MaterializedSource containing: `root_path` (absolute Path), `source_id` (string), `fingerprint` (string), and optional `metadata` (dict).

#### Scenario: MaterializedSource fields
- **WHEN** a provider resolves a source
- **THEN** the returned MaterializedSource has a valid absolute root_path pointing to an existing directory

### Requirement: Provider registry
The system SHALL support registering multiple SourceProviders and dispatching resolution through a SourceResolver service.

#### Scenario: Register and resolve
- **WHEN** a LocalDirProvider is registered and a local_dir source is resolved
- **THEN** the SourceResolver delegates to LocalDirProvider and returns a MaterializedSource
