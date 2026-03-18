# variable-resolution Specification

## Purpose
TBD - created by archiving change variable-resolution. Update Purpose after archive.
## Requirements
### Requirement: Variable precedence chain
The system SHALL resolve variable values in the following precedence order (lowest to highest): variable defaults from definition, environment variables (`MIXY_VAR_` prefix), vars file values, per-source value overrides, CLI `--var` overrides. Interactive prompting fills in remaining unresolved required variables.

#### Scenario: CLI overrides env var
- **WHEN** env var `MIXY_VAR_PROJECT_NAME=env_name` is set and CLI passes `--var project_name=cli_name`
- **THEN** the resolved value is `cli_name`

#### Scenario: Default used when no override
- **WHEN** variable has `default: "3.12"` and no higher-precedence source provides a value
- **THEN** the resolved value is `"3.12"`

#### Scenario: Env var overrides default
- **WHEN** variable has `default: "3.11"` and `MIXY_VAR_PYTHON_VERSION=3.12` is set
- **THEN** the resolved value is `"3.12"`

#### Scenario: Vars file overrides env
- **WHEN** env provides a value and vars file also provides a value for the same variable
- **THEN** the vars file value wins

### Requirement: Type coercion
The system SHALL coerce resolved string values to the declared variable type (str, int, float, bool).

#### Scenario: Coerce string to int
- **WHEN** variable has `type: int` and resolved value is `"42"`
- **THEN** the final value is the integer `42`

#### Scenario: Coerce string to bool
- **WHEN** variable has `type: bool` and resolved value is `"true"`
- **THEN** the final value is `True`

#### Scenario: Coercion failure
- **WHEN** variable has `type: int` and resolved value is `"not_a_number"`
- **THEN** the system raises a `VariableResolutionError` with the variable name and attempted value

### Requirement: Constraint validation
The system SHALL validate resolved values against `choices` and `pattern` constraints defined on the variable.

#### Scenario: Value not in choices
- **WHEN** variable has `choices: ["3.10", "3.11", "3.12"]` and resolved value is `"3.9"`
- **THEN** the system raises a `VariableResolutionError` listing valid choices

#### Scenario: Value does not match pattern
- **WHEN** variable has `pattern: "^[a-z_]+$"` and resolved value is `"My-Project"`
- **THEN** the system raises a `VariableResolutionError` showing the pattern

### Requirement: Interactive prompting for unresolved required variables
In interactive mode, the system SHALL prompt the user for any required variable that remains unresolved after all other sources are checked.

#### Scenario: Prompt for missing required variable
- **WHEN** variable is `required: true`, has no default, and no value from any source
- **THEN** the system prompts the user with the variable description and accepts input

#### Scenario: Non-interactive mode fails on missing required
- **WHEN** `--non-interactive` flag is set and a required variable has no value
- **THEN** the system raises a `VariableResolutionError` listing all unresolved required variables

### Requirement: Prompting is owned by the application layer
The application layer SHALL own interactive prompting and secret masking concerns while the domain resolver remains focused on precedence, coercion, and validation.

#### Scenario: Missing variable is surfaced to the application layer
- **WHEN** the domain resolver encounters a required variable with no resolved value
- **THEN** it raises a `VariableResolutionError` that the application layer can use to prompt the user or fail non-interactively

#### Scenario: Prompt shows choices
- **WHEN** prompting for a variable with `choices: ["a", "b", "c"]`
- **THEN** the prompt displays the available choices

### Requirement: Secret variable masking
The system SHALL mask values of variables marked `secret: true` in all log output, replacing them with `***`.

#### Scenario: Secret value in logs
- **WHEN** a secret variable `db_password` is resolved to `"hunter2"`
- **THEN** all log output referencing this value shows `***` instead of `hunter2`

### Requirement: Per-source variable context
The system SHALL support per-source value overrides that apply only when rendering that specific source's templates.

#### Scenario: Per-source override
- **WHEN** global `values` sets `port: 8080` and source "api" sets `values: {port: 3000}`
- **THEN** rendering source "api" uses `port: 3000` while other sources use `port: 8080`
