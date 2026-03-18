## ADDED Requirements

### Requirement: Planning and generation use explicit application composition
The application SHALL assemble default planning and generation collaborators through an explicit composition path rather than creating concrete adapters ad hoc inside use cases.

#### Scenario: Running planning with default dependencies
- **WHEN** the CLI invokes planning or generation without dependency overrides
- **THEN** the use cases receive their default collaborators from one explicit composition path
