## Why

Generation still stops on first write failure after partially mutating the output tree. That is the main remaining reliability gap in the runtime, but changing it may introduce new behavior and complexity. It needs an explicit change rather than an opportunistic refactor.

## What Changes

- Define Mixy's write-failure contract explicitly and keep the current partial-write execution model
- Document that generation stops on the first write failure with no rollback or cleanup guarantee
- Add or tighten failure-path validation so the preserved behavior is deliberate and test-backed

## Capabilities

### New Capabilities
- `execution-atomicity`: Explicit execution guarantees for write failures

## Impact

- Preserves current runtime behavior on filesystem failures
- Makes the reliability contract explicit for users and future changes
