## Why

`plan_project` and `generate_project` still assemble concrete adapters directly. That keeps application composition implicit and makes it harder to reuse the planning pipeline with different runtimes or test doubles.

## What Changes

- Introduce missing application ports around planning/generation dependencies
- Add a small composition root that wires default runtime implementations
- Keep use-case behavior stable while reducing direct adapter coupling

## Capabilities

### New Capabilities
- `planning-composition-root`: Explicit application dependency assembly for planning and generation

## Impact

- Adds application ports and a default runtime composition path
- Refactors use cases to depend on assembled collaborators rather than ad hoc imports
