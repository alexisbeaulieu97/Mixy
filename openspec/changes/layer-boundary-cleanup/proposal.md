## Why

`mixy/domain/services/` still contains impure orchestration-facing services that depend on infrastructure details. `SourceResolver` imports the provider protocol from `mixy.infrastructure.sources.base`, and `TemplateRenderer` imports binary detection and Jinja helpers directly from infrastructure rendering modules. That means the nominal domain layer is still coupled to infrastructure concerns.

## What Changes

- Move source-resolution and template-rendering ownership into the application layer
- Define the source-provider contract in `mixy/application/ports/` and make infrastructure providers implement that contract
- Update the shared planning and generation flows to depend on application-layer services instead of domain-layer impure services
- Keep behavior stable while reducing misleading domain/infrastructure coupling

## Capabilities

### New Capabilities
- `application-service-ownership`: Application-owned source resolution and template rendering services with application-owned provider contracts

### Modified Capabilities
- `project-planning-use-case`: Shared planning flow uses application-layer services for impure orchestration concerns

## Impact

- Adds application-layer ports and services modules
- Refactors imports across use cases, plugins, and tests to use the new ownership boundaries
- Reduces `mixy/domain/services/` to pure policy-oriented services
