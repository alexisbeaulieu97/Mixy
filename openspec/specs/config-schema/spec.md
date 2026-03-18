# config-schema Specification

## Purpose
TBD - created by archiving change domain-models-and-config. Update Purpose after archive.
## Requirements
### Requirement: Project config YAML schema
The system SHALL accept a YAML configuration file with the following top-level fields: `version` (required string), `name` (optional string), `description` (optional string), `sources` (required list), `values` (optional map), and `output` (optional map).

#### Scenario: Parse minimal valid config
- **WHEN** a YAML file contains `version: "1"` and `sources: [{id: base, source: {type: local_dir, path: ./templates}}]`
- **THEN** the system parses it into a valid ProjectDefinition with one source

#### Scenario: Reject config without version
- **WHEN** a YAML file is missing the `version` field
- **THEN** the system raises a validation error indicating version is required

#### Scenario: Reject unknown version
- **WHEN** a YAML file has `version: "99"`
- **THEN** the system raises an error indicating unsupported config version

### Requirement: Source definition as discriminated union
The system SHALL support source definitions discriminated by a `type` field with values: `local_dir`, `local_file`, `git`. Each type SHALL validate its own required fields.

#### Scenario: Parse local_dir source
- **WHEN** a source has `type: local_dir` and `path: ./templates`
- **THEN** it is parsed as a LocalDirSource with the path field

#### Scenario: Parse git source
- **WHEN** a source has `type: git`, `url`, and `ref` fields
- **THEN** it is parsed as a GitSource with url, ref, and optional subpath

#### Scenario: Reject source with unknown type
- **WHEN** a source has `type: s3_bucket`
- **THEN** the system raises a validation error listing valid source types

### Requirement: Variable definition model
The system SHALL support variable definitions with fields: `type` (str, int, float, bool), `required` (bool, default true), `default` (optional), `description` (optional string), `choices` (optional list), `pattern` (optional regex string), `secret` (bool, default false).

#### Scenario: Parse variable with all fields
- **WHEN** a variable definition includes type, required, default, description, choices, and pattern
- **THEN** all fields are correctly populated on the VariableDefinition model

#### Scenario: Default required to true
- **WHEN** a variable definition omits the `required` field
- **THEN** required defaults to true

### Requirement: Output definition model
The system SHALL support an output definition with fields: `path` (required string) and `conflict_policy` (enum: fail, overwrite, skip; default: fail).

#### Scenario: Default conflict policy
- **WHEN** output definition omits `conflict_policy`
- **THEN** it defaults to `fail`

### Requirement: Relative path resolution
The system SHALL resolve all relative paths in the config file relative to the config file's parent directory.

#### Scenario: Resolve source path relative to config
- **WHEN** config at `/home/user/project/mixy.yml` has source path `./templates`
- **THEN** the resolved path is `/home/user/project/templates`

