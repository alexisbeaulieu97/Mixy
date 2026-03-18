## ADDED Requirements

### Requirement: Canonical application-layer ownership
The repo SHALL treat application-layer service and port modules as the canonical import locations for source resolution, template rendering, and source-provider contracts.

#### Scenario: Canonical import paths are documented
- **WHEN** a contributor looks for the ownership boundary of source providers or impure planning services
- **THEN** the repo points them to the application-layer modules as the canonical paths

### Requirement: Legacy shim paths are not reintroduced
The repo SHALL fail a boundary regression check if source files import retired shim paths.

#### Scenario: Boundary test rejects legacy service imports
- **WHEN** a repo Python file imports `mixy.domain.services.source_resolver` or `mixy.domain.services.template_renderer`
- **THEN** the boundary regression test fails

#### Scenario: Boundary test rejects legacy provider-contract imports
- **WHEN** a repo Python file imports `mixy.infrastructure.sources.base`
- **THEN** the boundary regression test fails
