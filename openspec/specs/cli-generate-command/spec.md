# cli-generate-command Specification

## Purpose
TBD - created by archiving change cli-commands-and-ux. Update Purpose after archive.
## Requirements
### Requirement: Generate command
The CLI SHALL provide `mixy generate CONFIG_PATH` that runs the full generation pipeline.

#### Scenario: Basic generation
- **WHEN** user runs `mixy generate mixy.yml`
- **THEN** the system generates the project to the configured output path

#### Scenario: Output override
- **WHEN** user runs `mixy generate mixy.yml --output /tmp/out`
- **THEN** the output is written to `/tmp/out`

#### Scenario: Variable override
- **WHEN** user runs `mixy generate mixy.yml --var name=foo --var version=1.0`
- **THEN** variables `name` and `version` are set to the provided values

#### Scenario: Vars file
- **WHEN** user runs `mixy generate mixy.yml --vars-file vars.yml`
- **THEN** variable values are loaded from `vars.yml`

#### Scenario: Dry run
- **WHEN** user runs `mixy generate mixy.yml --dry-run`
- **THEN** the plan is displayed without writing files

#### Scenario: Non-interactive mode
- **WHEN** user runs `mixy generate mixy.yml --non-interactive`
- **THEN** the system fails on unresolved required variables instead of prompting

#### Scenario: Overwrite flag
- **WHEN** user runs `mixy generate mixy.yml --overwrite`
- **THEN** the conflict policy is set to `overwrite` regardless of config setting

