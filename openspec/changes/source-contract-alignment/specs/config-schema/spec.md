## MODIFIED Requirements

### Requirement: Source definition as discriminated union
The system SHALL support source definitions discriminated by a `type` field with values: `local_dir`, `git`. Each type SHALL validate its own required fields.

#### Scenario: Parse local_dir source
- **WHEN** a source has `type: local_dir` and `path: ./templates`
- **THEN** it is parsed as a LocalDirSource with the path field

#### Scenario: Parse git source
- **WHEN** a source has `type: git`, `url`, and `ref` fields
- **THEN** it is parsed as a GitSource with url, ref, and optional subpath

#### Scenario: Reject unsupported local_file source
- **WHEN** a source has `type: local_file`
- **THEN** the system raises a validation error indicating that the supported source types are `local_dir` and `git`
