## Context

The first migration wave fixed several runtime mismatches, but not all active specs were updated with those corrections. This change should bring the artifacts back in line with the current implementation so future work does not start from stale assumptions.

## Goals / Non-Goals

**Goals:**
- Align active OpenSpec specs and docs with the current runtime
- Remove known stale statements such as `local_file` support or a shell `git` dependency where those no longer apply
- Keep the change documentation-only unless a narrow runtime correction is required

**Non-Goals:**
- Reworking runtime behavior under the guise of documentation cleanup
- Rewriting archived historical artifacts
- Broadening into contract decisions that belong to other queued changes

## Decisions

### Active artifacts matter more than historical ones
Archived changes remain historical records. This change should correct active specs and docs first.

### Prefer documentation-only updates
If runtime and tests already agree, change the artifacts rather than reopening code.

## Implementation Outline

1. Audit active specs and docs against current code and tests.
2. Update mismatched active artifacts.
3. Archive or annotate completed change artifacts where helpful for workflow clarity.

## Risks / Trade-offs

- Documentation-only changes can still affect workflow decisions, so the audit must be evidence-based.
