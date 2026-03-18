# cli-error-formatting Specification

## Purpose
TBD - created by archiving change cli-commands-and-ux. Update Purpose after archive.
## Requirements
### Requirement: User-friendly error messages
The CLI SHALL catch domain exceptions and format them as readable error messages with context and suggestions.

#### Scenario: Config validation error
- **WHEN** a ConfigValidationError is raised during generation
- **THEN** the CLI displays the error type, field path, message, and suggestion

#### Scenario: Source resolution error
- **WHEN** a SourceResolutionError is raised
- **THEN** the CLI displays the source ID, error message, and exit code 1

#### Scenario: Unexpected error
- **WHEN** an unhandled exception occurs
- **THEN** the CLI displays a generic error message and suggests running with `--log-level debug`

### Requirement: Exit codes
The CLI SHALL exit with code 0 on success, 1 on user errors (bad config, missing variable), and 2 on system errors (git unavailable, permission denied).

#### Scenario: Exit code on success
- **WHEN** generation completes successfully
- **THEN** exit code is 0

#### Scenario: Exit code on user error
- **WHEN** config validation fails
- **THEN** exit code is 1

#### Scenario: Exit code on system error
- **WHEN** git is not available for a git source
- **THEN** exit code is 2

