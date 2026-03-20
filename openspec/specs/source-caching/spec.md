# source-caching Specification

## Purpose
TBD - created by archiving change git-source-and-caching. Update Purpose after archive.
## Requirements
### Requirement: Cache store for Git repositories
The system SHALL cache Git repository snapshots and extracted content snapshots under the platformdirs user cache directory.

#### Scenario: First clone is cached
- **WHEN** a Git source is resolved for the first time
- **THEN** the repository snapshot is stored in the cache and the materialized snapshot is stored by URL+SHA

#### Scenario: Cache hit on second resolve
- **WHEN** the same Git source with the same resolved SHA is requested again
- **THEN** the cached materialized snapshot is returned without re-cloning or re-extracting

#### Scenario: Cache miss on new commit
- **WHEN** the same URL is requested but the branch points to a new commit
- **THEN** the provider fetches updates to the cached repository snapshot and materializes the new commit

### Requirement: Cache list command
The CLI SHALL provide `mixy cache list` showing all cached entries with repository URL, ref, resolved SHA, and disk size.

#### Scenario: List cached entries
- **WHEN** user runs `mixy cache list`
- **THEN** the system displays a table of cached repos with URL, ref, SHA, and size

#### Scenario: Empty cache
- **WHEN** user runs `mixy cache list` with no cached entries
- **THEN** the system displays a message indicating the cache is empty

### Requirement: Cache clear command
The CLI SHALL provide `mixy cache clear` to remove cached entries.

#### Scenario: Clear all cache
- **WHEN** user runs `mixy cache clear`
- **THEN** all cached repos and extracted content are removed

#### Scenario: Clear specific entry
- **WHEN** user runs `mixy cache clear --url https://github.com/example/template.git`
- **THEN** only the cache entries for that URL are removed
