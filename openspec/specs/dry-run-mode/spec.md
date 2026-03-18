# dry-run-mode Specification

## Purpose
TBD - created by archiving change generation-pipeline. Update Purpose after archive.
## Requirements
### Requirement: Dry-run mode
The system SHALL support a `--dry-run` flag that builds the full merge plan and displays it without writing any files.

#### Scenario: Dry-run shows planned operations
- **WHEN** user runs `mixy generate config.yml --dry-run`
- **THEN** the system displays a table of planned operations (action, output path, source) and writes no files

#### Scenario: Dry-run detects conflicts
- **WHEN** user runs `mixy generate config.yml --dry-run` and merge conflicts exist
- **THEN** the system displays the conflicts in the plan output

#### Scenario: Dry-run exits with success
- **WHEN** dry-run completes with no errors
- **THEN** the exit code is 0

