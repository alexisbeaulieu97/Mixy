# cli-inspect-command Specification

## Purpose
TBD - created by archiving change cli-commands-and-ux. Update Purpose after archive.
## Requirements
### Requirement: Inspect command
The CLI SHALL provide `mixy inspect CONFIG_PATH` that shows the resolved configuration state.

#### Scenario: Show resolved variables
- **WHEN** user runs `mixy inspect mixy.yml`
- **THEN** the output includes a table of variables with name, type, resolved value, and value source

#### Scenario: Show source list
- **WHEN** user runs `mixy inspect mixy.yml`
- **THEN** the output includes a list of sources with id, type, and path/URL

#### Scenario: Show merge preview
- **WHEN** user runs `mixy inspect mixy.yml`
- **THEN** the output includes expected output file paths grouped by source

