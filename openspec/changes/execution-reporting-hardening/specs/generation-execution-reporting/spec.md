## ADDED Requirements

### Requirement: Explicit overwrite reporting
Generation execution SHALL report overwritten files separately from ordinary rendered files.

#### Scenario: Overwrite operations are counted distinctly
- **WHEN** execution applies an `Overwrite` operation
- **THEN** the result distinguishes that overwrite from ordinary rendered-file writes

### Requirement: Structured partial-failure reporting
Generation execution SHALL retain enough context about a failed filesystem operation to explain a partial execution result.

#### Scenario: Filesystem execution stops on a failed operation
- **WHEN** the executor encounters an `OSError` while applying a plan
- **THEN** the result records the failed target and enough operation context to explain what stopped execution

### Requirement: Truthful execution summaries
Execution summaries SHALL clearly reflect partial execution when failures occur.

#### Scenario: Summary includes overwrite and failure information
- **WHEN** a generation result includes overwrites or failures
- **THEN** the formatted summary reports overwrite counts and indicates that execution completed only partially if a failure occurred
