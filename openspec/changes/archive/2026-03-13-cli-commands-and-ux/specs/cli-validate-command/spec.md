## ADDED Requirements

### Requirement: Validate command
The CLI SHALL provide `mixy validate CONFIG_PATH` that checks config validity without generating files.

#### Scenario: Valid config
- **WHEN** user runs `mixy validate mixy.yml` and config is valid
- **THEN** the system prints a success message and exits with code 0

#### Scenario: Invalid config
- **WHEN** user runs `mixy validate mixy.yml` and config has errors
- **THEN** the system prints all validation errors and exits with code 1

#### Scenario: Multiple errors reported
- **WHEN** config has three validation issues
- **THEN** all three are displayed, not just the first
