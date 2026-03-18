# git-source Specification

## Purpose
TBD - created by archiving change git-source-and-caching. Update Purpose after archive.
## Requirements
### Requirement: Git repository source resolution
The GitSourceProvider SHALL resolve `git` source definitions by cloning the repository and checking out the specified ref.

#### Scenario: Clone and resolve branch ref
- **WHEN** source has `type: git`, `url: https://github.com/example/template.git`, `ref: main`
- **THEN** the provider clones the repo, resolves `main` to a commit SHA, and returns a MaterializedSource

#### Scenario: Resolve tag ref
- **WHEN** source has `ref: v1.2.0`
- **THEN** the provider resolves the tag to a commit SHA and extracts that version

#### Scenario: Resolve commit SHA
- **WHEN** source has `ref: abc123def` (a commit SHA)
- **THEN** the provider verifies the SHA exists and extracts that commit

#### Scenario: Extract subpath
- **WHEN** source has `subpath: template/python`
- **THEN** the MaterializedSource root_path points to the `template/python` subdirectory within the extracted content

#### Scenario: Invalid subpath
- **WHEN** source has `subpath: nonexistent/path` that does not exist in the repo
- **THEN** the provider raises a `SourceResolutionError` identifying the missing subpath

### Requirement: Git integration does not require a shell `git` binary
The system SHALL perform Git source resolution through the current Python-backed integration path and not require a shell `git` executable on PATH.

#### Scenario: Git source resolution
- **WHEN** a `git` source is resolved
- **THEN** the provider uses the configured Git integration path rather than shelling out to `git`

### Requirement: Git fetch and update
The GitSourceProvider SHALL fetch updates for already-cloned repositories to handle moved branches and new tags.

#### Scenario: Branch moved to new commit
- **WHEN** a cached repo exists but the branch `main` has new commits
- **THEN** the provider fetches updates, resolves the new SHA, and extracts the updated content

### Requirement: Git source fingerprint
The GitSourceProvider SHALL produce a fingerprint based on the repository URL and resolved commit SHA.

#### Scenario: Same URL and commit
- **WHEN** fingerprint is computed for the same repo URL and commit SHA
- **THEN** the fingerprint is identical across invocations
