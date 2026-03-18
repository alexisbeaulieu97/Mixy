## Why

`mixy generate` and `mixy inspect` currently duplicate the same config-loading, validation, variable-resolution, source-resolution, and render-planning flow. That duplication has already diverged on provider assembly and output fallback behavior, which makes later refactors riskier than they need to be.

## What Changes

- Add a shared application use case that loads a project, resolves inputs, and produces reusable planning state for both `inspect` and `generate`
- Build render planning through one shared application path instead of duplicating orchestration in the CLI layer
- Make `inspect` and `generate` obtain source providers from the same pluggy-backed registry path by default
- Preserve current CLI output and dry-run behavior while reducing orchestration duplication

## Capabilities

### New Capabilities
- `project-planning-use-case`: Shared application planning flow that prepares and plans a project for multiple command consumers

### Modified Capabilities

## Impact

- Adds a new application use case under `mixy/application/use_cases/`
- Refactors `mixy/application/use_cases/generate_project.py` into a thinner execution wrapper
- Refactors `mixy/cli/commands/inspect.py` to consume the shared planning path
- Adds tests covering shared provider-registry usage and planning behavior preservation
