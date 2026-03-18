## ADDED Requirements

### Requirement: Application-owned planning defaults
The system SHALL assemble default planning and generation collaborators through application-owned contracts instead of importing infrastructure defaults directly inside application use cases and services.

#### Scenario: Using default planning dependencies
- **WHEN** application code invokes planning, generation, or validation without custom collaborators
- **THEN** the default runtime dependencies are assembled through `mixy/application/composition.py`
- **AND** the public use-case behavior remains unchanged

### Requirement: Infrastructure adapters remain swappable
The system SHALL keep infrastructure config loading, metadata discovery, provider discovery, prompting, and secret masking behind narrow application-owned seams.

#### Scenario: Injecting alternate collaborators
- **WHEN** tests or future runtimes provide alternate loaders, registries, or masking implementations
- **THEN** application use cases and services accept those collaborators without importing infrastructure implementations directly
