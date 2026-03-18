## Why

`mixy/domain/services/variable_resolver.py` still owns two interface-facing concerns that do not belong in the domain layer:

- prompting for missing required values through Typer
- configuring global Loguru secret masking as a side effect of resolution

That makes the core resolver stateful, harder to test in isolation, and less reusable outside the CLI path. The next bounded change should extract those concerns into application/interface-owned seams while preserving variable precedence and CLI behavior.

## What Changes

- Make the domain `VariableResolver` pure from the standpoint of prompting and logging side effects
- Introduce an application-owned variable-resolution service that coordinates optional prompting through a `PromptGateway`
- Move secret masking side effects into an infrastructure logging helper used by the application layer
- Update planning flows and tests to preserve existing prompting, masking, and variable-precedence behavior

## Capabilities

### New Capabilities
- `variable-resolution-boundary`: Application-owned prompting and secret masking around a pure domain variable resolver

### Modified Capabilities
- `project-planning-use-case`: Shared planning flow uses the application-owned variable-resolution seam instead of domain-owned prompting/logging behavior

## Impact

- Adds application/infrastructure seams for prompting and secret masking
- Refactors project planning to depend on the new application-owned service
- Preserves CLI flags, variable precedence, and rendered output behavior
