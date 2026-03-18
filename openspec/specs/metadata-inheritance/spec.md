# metadata-inheritance Specification

## Purpose
TBD - created by archiving change recursive-template-metadata. Update Purpose after archive.
## Requirements
### Requirement: Scope hierarchy resolution
The system SHALL resolve effective metadata for each file by merging scopes from project defaults → source root → nested directories → file scope.

#### Scenario: File scope overrides directory scope
- **WHEN** directory metadata sets `copy_mode: render` and file sidecar sets `copy_mode: raw`
- **THEN** the effective copy_mode for that file is `raw`

#### Scenario: Nested directory refines root
- **WHEN** root metadata sets `render.undefined: strict` and nested directory metadata does not override it
- **THEN** the nested directory inherits `render.undefined: strict`

### Requirement: Scalar inheritance — nearest scope wins
For scalar fields (`copy_mode`, `render.undefined`, `render.path_names`), the nearest scope's value SHALL override parent scope values.

#### Scenario: Scalar override
- **WHEN** root sets `render.path_names: true` and subdirectory sets `render.path_names: false`
- **THEN** files in the subdirectory use `render.path_names: false`

### Requirement: List inheritance — union by default
For list fields (`exclude`, `include`), child scope lists SHALL be unioned with parent scope lists unless `_replace: true` is set.

#### Scenario: Exclude list union
- **WHEN** root excludes `["*.png"]` and subdirectory excludes `["*.jpg"]`
- **THEN** files in the subdirectory have effective exclude `["*.png", "*.jpg"]`

#### Scenario: Exclude list replace
- **WHEN** root excludes `["*.png"]` and subdirectory has `exclude: ["*.gif"]` with `_replace: true`
- **THEN** files in the subdirectory have effective exclude `["*.gif"]` only

### Requirement: Map inheritance — deep merge
For map fields (`render`, `variables`), child scope maps SHALL deep merge with parent maps, child keys overriding at the leaf level.

#### Scenario: Render map merge
- **WHEN** root sets `render: {text_files: true, path_names: true}` and subdirectory sets `render: {path_names: false}`
- **THEN** effective render is `{text_files: true, path_names: false}`

### Requirement: Variable refinement validation
Nested scope variable definitions SHALL be compatible with parent definitions. Type changes, secret flag changes, and incompatible choice constraints SHALL be rejected.

#### Scenario: Valid refinement — add description
- **WHEN** root defines variable `name` with `type: str` and subdirectory adds `description: "Project name"`
- **THEN** the refinement is accepted

#### Scenario: Invalid refinement — type change
- **WHEN** root defines variable `port` with `type: int` and subdirectory redefines it as `type: str`
- **THEN** the system raises a `MetadataConflictError` showing the parent and child definitions

#### Scenario: Invalid refinement — incompatible choices
- **WHEN** root defines `choices: ["a", "b"]` and child defines `choices: ["x", "y"]`
- **THEN** the system raises a `MetadataConflictError`

