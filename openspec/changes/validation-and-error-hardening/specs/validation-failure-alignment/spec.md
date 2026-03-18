## ADDED Requirements

### Requirement: Early failure for blocking local source validation
Semantic validation SHALL treat missing local directory sources as blocking validation errors.

#### Scenario: Validate fails on a missing local source path
- **WHEN** a config references a `local_dir` source path that does not exist
- **THEN** `mixy validate` exits as a user error and reports the path issue as an error instead of a warning

#### Scenario: Planning fails before source resolution on a missing local source path
- **WHEN** `mixy inspect` or `mixy generate` receives a config whose `local_dir` source path does not exist
- **THEN** planning fails with config validation output instead of continuing into later source-resolution failure

### Requirement: Consistent user-facing validation failure behavior
Commands that operate on a config SHALL align on exit behavior for blocking validation issues.

#### Scenario: Blocking validation issues exit with code one
- **WHEN** `mixy validate`, `mixy inspect`, or `mixy generate` encounters a blocking validation issue
- **THEN** the command exits with user error semantics and surfaces the validation problem to the user

### Requirement: Covered CLI error formatting branches
The CLI SHALL have focused test coverage for representative error-formatting and exit-code mapping branches.

#### Scenario: Config validation and runtime errors remain formatted readably
- **WHEN** the CLI formats representative `ConfigValidationError`, `SourceResolutionError`, `RenderingError`, and unexpected errors
- **THEN** the output remains readable and the mapped exit codes remain correct
