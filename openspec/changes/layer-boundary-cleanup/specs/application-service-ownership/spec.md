## ADDED Requirements

### Requirement: Application-owned source provider contract
The application SHALL own the source-provider contract used by source resolution and plugin registration.

#### Scenario: Infrastructure providers implement an application port
- **WHEN** Mixy registers or uses a source provider
- **THEN** the provider contract is defined in the application layer and implemented by infrastructure providers

### Requirement: Application-owned impure planning services
Impure services used by project planning SHALL live in the application layer instead of the domain layer.

#### Scenario: Planning uses application services for source resolution
- **WHEN** project preparation resolves template sources
- **THEN** it depends on an application-layer `SourceResolver`

#### Scenario: Planning uses application services for template rendering
- **WHEN** project planning renders template files and output paths
- **THEN** it depends on an application-layer `TemplateRenderer`

### Requirement: Behavior-preserving boundary migration
The ownership migration SHALL preserve existing source resolution and template rendering behavior.

#### Scenario: Existing resolver behavior remains unchanged
- **WHEN** source resolution is exercised through the shared planning flow or direct resolver tests
- **THEN** the same sources resolve, suggestions remain intact, and template reference subpaths still apply

#### Scenario: Existing renderer behavior remains unchanged
- **WHEN** template rendering is exercised through renderer tests and generation planning tests
- **THEN** binary detection, render policy handling, Jinja rendering, and output-path rendering still behave the same
