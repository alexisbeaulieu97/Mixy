# merge-planning Specification

## Purpose
TBD - created by archiving change merge-planner. Update Purpose after archive.
## Requirements
### Requirement: Deterministic source ordering
The MergePlanner SHALL process sources in the order they are declared in the configuration file.

#### Scenario: Two sources with no conflicts
- **WHEN** source A declares `README.md` and source B declares `setup.py`
- **THEN** the plan contains operations for both files in source declaration order

#### Scenario: Source order determines overwrite winner
- **WHEN** conflict_policy is `overwrite`, source A and source B both declare `README.md`, and A is declared before B
- **THEN** source B's `README.md` is used (later source wins)

### Requirement: Recursive directory merging
The MergePlanner SHALL merge directories recursively when multiple sources contribute to the same directory path.

#### Scenario: Merge directories from two sources
- **WHEN** source A contains `src/utils.py` and source B contains `src/main.py`
- **THEN** the plan creates `src/` and includes both files

### Requirement: File conflict detection
The MergePlanner SHALL detect when two or more sources produce a file at the same output path.

#### Scenario: Detect file conflict
- **WHEN** source A and source B both produce `README.md`
- **THEN** the planner identifies this as a conflict

#### Scenario: Report all conflicts
- **WHEN** multiple file conflicts exist
- **THEN** the planner reports all conflicts, not just the first

### Requirement: Conflict policy enforcement
The MergePlanner SHALL apply the configured conflict policy: `fail` (raise error), `overwrite` (later source wins), `skip` (earlier source wins).

#### Scenario: Fail policy
- **WHEN** conflict_policy is `fail` and a file conflict exists
- **THEN** the planner raises a `MergeConflictError` listing all conflicting paths and their sources

#### Scenario: Overwrite policy
- **WHEN** conflict_policy is `overwrite` and source A and B both produce `config.yml`
- **THEN** the plan contains an Overwrite operation using source B's file

#### Scenario: Skip policy
- **WHEN** conflict_policy is `skip` and source A and B both produce `config.yml`
- **THEN** the plan contains a SkipExisting operation, keeping source A's file

### Requirement: File-vs-directory conflict always fails
The MergePlanner SHALL always fail when one source produces a file at a path and another source produces a directory at the same path, regardless of conflict policy.

#### Scenario: File-vs-directory conflict
- **WHEN** source A has `docs` as a file and source B has `docs/` as a directory
- **THEN** the planner raises a `MergeConflictError` regardless of conflict policy

### Requirement: RenderPlan output
The MergePlanner SHALL produce a `RenderPlan` containing: the ordered list of `FileOperation` objects, a list of detected `Conflict` objects, the effective conflict policy, and the output path.

#### Scenario: RenderPlan contains all operations
- **WHEN** three sources are merged with no conflicts
- **THEN** the RenderPlan's operations list contains every file from all three sources

#### Scenario: Dry-run inspectable plan
- **WHEN** a RenderPlan is built
- **THEN** it can be inspected to list all planned output paths without executing any writes

