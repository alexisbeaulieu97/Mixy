## ADDED Requirements

### Requirement: Shared project planning use case
The application SHALL provide a shared planning flow that loads configuration, validates it, resolves variables, resolves sources, computes render decisions, and builds a merge plan for command consumers.

#### Scenario: Prepare and plan for generation
- **WHEN** the generation flow requests a plan for a valid config
- **THEN** the application returns a reusable project planning result containing the resolved project state and merge plan before execution begins

#### Scenario: Prepare and plan for inspection
- **WHEN** the inspect flow requests a plan for a valid config
- **THEN** the application returns the same planning result shape without duplicating orchestration in the CLI command

### Requirement: Shared provider registry path
Commands that depend on project planning SHALL use the same default source-provider registry path.

#### Scenario: Use plugin-backed providers for generate and inspect
- **WHEN** `mixy generate` and `mixy inspect` resolve source providers without explicit dependency overrides
- **THEN** both commands obtain providers from the same registry assembly path

### Requirement: Configurable output fallback during planning
The shared planning flow SHALL support command-specific output fallback behavior without changing planning semantics.

#### Scenario: Generate requires an output path
- **WHEN** the generation flow plans a config with no configured output path and no override
- **THEN** the application reports an error instead of building a merge plan

#### Scenario: Inspect can preview without a configured output path
- **WHEN** the inspect flow plans a config with no configured output path and no override
- **THEN** the application builds the merge preview against a placeholder output path
