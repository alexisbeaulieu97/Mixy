## Why

The application layer still imports several infrastructure defaults directly. `plan_project(...)` and `generate_project(...)` default to infrastructure config loaders, metadata discovery, and vars loading. `VariableResolutionService` still defaults to the Typer prompt adapter and process-global secret masking implementation. `composition.py` also reaches directly into plugin discovery to fetch providers. That means the package layout says "application-owned orchestration", but the runtime still hardwires infrastructure concerns inside application modules.

## What Changes

- Introduce the minimal remaining application-owned ports for config loading, vars loading, metadata discovery, source provider registry, and secret masking
- Move default runtime wiring for those collaborators into `mixy/application/composition.py`
- Refactor planning/generation use cases and variable-resolution service to depend on application-owned contracts or injected collaborators instead of direct infrastructure imports
- Preserve runtime behavior and CLI semantics

## Capabilities

### New Capabilities
- `planning-infrastructure-port-completion`: Application-owned dependency seams for planning and generation defaults

## Impact

- Refactors dependency assembly and internal imports only
- Preserves CLI behavior, config schema, rendering semantics, and generation output
- Improves testability and makes the existing architecture boundaries real
