# generation-pipeline Specification

## Purpose
TBD - created by archiving change generation-pipeline. Update Purpose after archive.
## Requirements
### Requirement: End-to-end project generation
The system SHALL generate a project directory from a configuration file by executing the full pipeline: load config, validate, resolve variables, resolve sources, build merge plan, execute file operations.

#### Scenario: Generate from minimal config with local source
- **WHEN** user runs `mixy generate config.yml` with a valid config pointing to a local directory source
- **THEN** the system creates the output directory with all rendered and copied files

#### Scenario: Generate with variable overrides
- **WHEN** user runs `mixy generate config.yml --var project_name=myapp`
- **THEN** all templates render with `project_name` set to `myapp`

#### Scenario: Generate with output path override
- **WHEN** user runs `mixy generate config.yml --output /tmp/myproject`
- **THEN** the output is written to `/tmp/myproject` instead of the config's output path

### Requirement: Pipeline fails before writes on validation error
The system SHALL complete all validation, resolution, and planning before writing any files. If any stage fails, no files are written.

#### Scenario: Config validation error
- **WHEN** config has duplicate source IDs
- **THEN** the system reports the error and writes no files

#### Scenario: Merge conflict with fail policy
- **WHEN** merge planning detects conflicts with fail policy
- **THEN** the system reports all conflicts and writes no files

#### Scenario: Unresolved required variable in non-interactive mode
- **WHEN** a required variable has no value and `--non-interactive` is set
- **THEN** the system reports the missing variable and writes no files

### Requirement: Generation failure may leave partial output
The system SHALL stop filesystem execution at the first write failure and report the failure without guaranteeing rollback or cleanup of already-written output.

#### Scenario: Write failure during generation
- **WHEN** a filesystem write fails after some output has already been written
- **THEN** the executor stops at the failed operation
- **AND** earlier files or directories remain on disk
- **AND** the failure report identifies the failed operation and target path

### Requirement: Generation summary
After successful generation, the system SHALL print a summary showing counts of directories created, files rendered, files copied raw, and files skipped.

#### Scenario: Summary after generation
- **WHEN** generation completes successfully
- **THEN** the system prints a summary with operation counts and the output path
