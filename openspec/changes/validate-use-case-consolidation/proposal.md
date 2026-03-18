## Why

`mixy validate` still bypasses the application layer and assembles its own load-and-validate path. That leaves one CLI command outside the same architecture seam used by planning and generation.

## What Changes

- Add an application-owned `validate_project` use case
- Move CLI validation onto that use case
- Keep exit behavior and validation output stable

## Capabilities

### New Capabilities
- `application-validate-use-case`: Shared application validation flow for CLI consumers

## Impact

- Reduces command-path drift by removing the last direct CLI validation orchestration path
- Preserves current validation output and exit semantics
