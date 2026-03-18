## ADDED Requirements

### Requirement: Application renderer depends on an adapter seam
The system SHALL make `TemplateRenderer` depend on an application-owned rendering adapter instead of importing infrastructure rendering helpers directly.

#### Scenario: Using default rendering behavior
- **WHEN** application code uses the default `TemplateRenderer`
- **THEN** composition assembles the default infrastructure-backed rendering adapter
- **AND** rendering behavior remains unchanged

### Requirement: Rendering semantics remain stable
The system SHALL preserve current file-rendering, path-rendering, binary-detection, and error-mapping behavior after the adapter boundary is introduced.

#### Scenario: Rendering templates after the boundary refactor
- **WHEN** the system renders template files and path segments
- **THEN** include/exclude policy, copy-mode behavior, Jinja suffix handling, and `RenderingError` behavior match the previous semantics
