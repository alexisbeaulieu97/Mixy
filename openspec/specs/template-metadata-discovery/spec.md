# template-metadata-discovery Specification

## Purpose
TBD - created by archiving change recursive-template-metadata. Update Purpose after archive.
## Requirements
### Requirement: Directory scope metadata discovery
The system SHALL discover `.mixy/template.yml` files at the root and within nested directories of a materialized source tree.

#### Scenario: Root metadata
- **WHEN** a source tree contains `.mixy/template.yml` at its root
- **THEN** the metadata is loaded and applies to all files in the source tree

#### Scenario: Nested directory metadata
- **WHEN** `src/.mixy/template.yml` exists within a source tree
- **THEN** the metadata applies to all files under `src/` and its subdirectories

#### Scenario: No metadata present
- **WHEN** a source tree contains no `.mixy/template.yml` files
- **THEN** project-level defaults apply to all files

### Requirement: File scope sidecar metadata discovery
The system SHALL discover `<filename>.mixy.yml` sidecar files adjacent to their target files.

#### Scenario: Sidecar metadata
- **WHEN** `Dockerfile.mixy.yml` exists adjacent to `Dockerfile`
- **THEN** the sidecar metadata applies to `Dockerfile` only

#### Scenario: Sidecar for .j2 file
- **WHEN** `config.yaml.j2.mixy.yml` exists adjacent to `config.yaml.j2`
- **THEN** the sidecar metadata applies to `config.yaml.j2`

### Requirement: Metadata files excluded from output
The system SHALL exclude `.mixy/` directories and `*.mixy.yml` files from the generated output.

#### Scenario: .mixy directory not in output
- **WHEN** a source tree contains `.mixy/template.yml`
- **THEN** the `.mixy/` directory does not appear in the generated output

#### Scenario: Sidecar file not in output
- **WHEN** a source tree contains `Dockerfile.mixy.yml`
- **THEN** `Dockerfile.mixy.yml` does not appear in the generated output

### Requirement: Disallowed fields in template metadata
The system SHALL reject template metadata containing disallowed fields: `source`, `output`, `cache`, `merge_strategy`, `hooks`, `imports`.

#### Scenario: Reject disallowed field
- **WHEN** `.mixy/template.yml` contains a `source` field
- **THEN** the system raises a `MetadataValidationError` identifying the disallowed field

