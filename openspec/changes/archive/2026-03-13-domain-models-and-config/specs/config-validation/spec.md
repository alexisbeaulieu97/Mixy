## ADDED Requirements

### Requirement: Unique source IDs
The config validator SHALL reject configurations where two or more sources share the same `id` value.

#### Scenario: Duplicate source IDs
- **WHEN** config contains two sources both with `id: base`
- **THEN** the system raises a validation error identifying the duplicate ID

### Requirement: Variable type consistency
The config validator SHALL reject configurations where a variable's `default` value does not match its declared `type`.

#### Scenario: String default for int variable
- **WHEN** a variable has `type: int` and `default: "hello"`
- **THEN** the system raises a validation error indicating type mismatch

### Requirement: Choices match variable type
The config validator SHALL reject configurations where `choices` values do not match the variable's declared `type`.

#### Scenario: Int choices for string variable
- **WHEN** a variable has `type: str` and `choices: [1, 2, 3]`
- **THEN** the system raises a validation error

### Requirement: Source path existence check
The config validator SHALL warn (not fail) when a local source path does not exist at validation time.

#### Scenario: Missing local directory
- **WHEN** a source references `path: ./nonexistent`
- **THEN** the system emits a warning but does not fail validation

### Requirement: Actionable error messages
All validation errors SHALL include the field path and a human-readable description of what is wrong and how to fix it.

#### Scenario: Error message format
- **WHEN** any validation error occurs
- **THEN** the error message includes the YAML path (e.g., `sources[0].source.type`) and a fix suggestion
