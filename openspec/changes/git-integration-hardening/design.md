## Context

The current Git runtime no longer depends on shelling out to `git`, but the archived spec and docs still describe a PATH dependency and one integration test still creates commits through the shell. That mismatch is now the only known remaining full-suite failure.

## Goals / Non-Goals

**Goals:**
- Make Git integration tests independent of shell `git` configuration
- Align Git source docs/spec language with the `pygit2` implementation
- Keep the change small and independently verifiable

**Non-Goals:**
- Replacing the `pygit2` implementation
- Reworking cache behavior or source-planning architecture
- Fixing unrelated CLI or render-pipeline concerns

## Decisions

### Use `pygit2` for local Git test fixtures
The integration fixture should create local repositories the same way the codebase already creates Git repositories in unit tests: through `pygit2`, with explicit signatures and commit creation. This avoids shell hooks, PATH assumptions, and signing-agent interference.

### Update the contract to describe the actual runtime
The Git source spec and docs should describe `pygit2` as the Git implementation path for Mixy instead of claiming a required `git` executable on PATH.

## Implementation Outline

1. Replace shell-based local repository setup in the Git cache integration test with a `pygit2` fixture.
2. Update docs/spec text that still claims shell `git` is required.
3. Run the Git-focused tests and the full suite to confirm the environment-sensitive failure is removed.

## Risks / Trade-offs

- The change is intentionally narrow; it improves reliability without changing the Git source provider’s public shape.
- Archived planning artifacts may still mention shell `git`; those remain historical and do not need to be rewritten.
