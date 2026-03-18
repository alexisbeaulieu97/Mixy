# local-dir-source Specification

## Purpose
TBD - created by archiving change source-resolution. Update Purpose after archive.
## Requirements
### Requirement: Local directory source resolution
The LocalDirProvider SHALL resolve `local_dir` source definitions by validating the path exists and is a directory, then returning a MaterializedSource pointing to that path.

#### Scenario: Resolve existing directory
- **WHEN** source definition has `type: local_dir` and `path` points to an existing directory
- **THEN** the provider returns a MaterializedSource with root_path set to the absolute resolved path

#### Scenario: Resolve with subpath
- **WHEN** source definition has `type: local_dir`, `path: ./templates`, and `subpath: python`
- **THEN** the provider returns a MaterializedSource with root_path set to `<resolved_path>/python`

#### Scenario: Directory does not exist
- **WHEN** source definition path points to a non-existent directory
- **THEN** the provider raises a `SourceResolutionError` with the missing path

#### Scenario: Path is a file not directory
- **WHEN** source definition path points to a file instead of a directory
- **THEN** the provider raises a `SourceResolutionError` indicating a directory was expected

### Requirement: Local directory fingerprint
The LocalDirProvider SHALL compute a fingerprint based on the directory's absolute path and its modification time.

#### Scenario: Same directory same fingerprint
- **WHEN** fingerprint is computed twice for the same unmodified directory
- **THEN** both calls return the same fingerprint string

