## MODIFIED Requirements

### Requirement: Git repository source resolution
The GitSourceProvider SHALL resolve `git` source definitions through the configured Git implementation and checking out the specified ref.

#### Scenario: Clone and resolve branch ref
- **WHEN** source has `type: git`, `url: https://github.com/example/template.git`, `ref: main`
- **THEN** the provider clones the repo, resolves `main` to a commit SHA, and returns a MaterializedSource

#### Scenario: Resolve tag ref
- **WHEN** source has `ref: v1.2.0`
- **THEN** the provider resolves the tag to a commit SHA and extracts that version

#### Scenario: Resolve commit SHA
- **WHEN** source has `ref: abc123def` (a commit SHA)
- **THEN** the provider verifies the SHA exists and extracts that commit

#### Scenario: Extract subpath
- **WHEN** source has `subpath: template/python`
- **THEN** the MaterializedSource root_path points to the `template/python` subdirectory within the extracted content

#### Scenario: Invalid subpath
- **WHEN** source has `subpath: nonexistent/path` that does not exist in the repo
- **THEN** the provider raises a `SourceResolutionError` identifying the missing subpath

### Requirement: Git runtime dependency
The system SHALL use the configured Git runtime implementation for source resolution without requiring a shell `git` executable on PATH.

#### Scenario: Git runtime available through dependencies
- **WHEN** Mixy's configured Git runtime dependencies are available
- **THEN** Git source operations proceed normally without checking for a shell `git` binary

### Requirement: Git integration tests are environment independent
Git integration tests SHALL create local repositories without relying on shell Git hooks, user signing configuration, or PATH-specific behavior.

#### Scenario: Run Git cache integration tests with shell Git hooks present
- **WHEN** the test environment has shell Git hooks or signing-agent configuration
- **THEN** the Git cache integration test still creates a local repository and passes
