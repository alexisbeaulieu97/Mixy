## Why

Mixy's Git path is implemented with `pygit2`, but one integration test still creates repositories through the shell `git` command and now fails in environments with signing-agent hooks. The change should harden Git integration so the tests and user-facing guidance match the actual runtime implementation.

## What Changes

- Rewrite the local Git integration fixture to create repositories without shelling out to `git commit`
- Align Git source documentation and specification with the `pygit2`-backed runtime instead of a `git on PATH` requirement
- Keep the change focused on Git integration reliability; do not broaden into unrelated pipeline refactors

## Capabilities

### New Capabilities

### Modified Capabilities
- `git-source`: align the Git source contract and tests with the `pygit2`-backed implementation

## Impact

- Modifies Git integration tests and helper code
- Updates Git source documentation/spec language
- Improves full-suite reliability in environments with shell Git hooks or signing-agent configuration
