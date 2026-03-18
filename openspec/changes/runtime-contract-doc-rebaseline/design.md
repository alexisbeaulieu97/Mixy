## Context

The earlier runtime/spec sync change aligned active specs and user docs, but the product PRD still mixes current runtime behavior with older or aspirational ideas. The current repo supports `local_dir` and `git` sources, rejects `merge_strategy` on source entries, uses `values` rather than per-source `variables` on `TemplateReference`, and does not expose several speculative fields described in the draft PRD. This change should bring the remaining secondary docs back in line.

## Goals / Non-Goals

**Goals:**
- Correct stale PRD text and any other remaining secondary docs that contradict the current runtime
- Keep the change documentation-only
- Prefer removing misleading current-tense statements over preserving aspirational design text as if it were implemented

**Non-Goals:**
- Rewriting archived planning artifacts
- Reopening runtime behavior or schema design decisions
- Turning the PRD into a detailed schema reference beyond what the current runtime supports

## Decisions

### Treat the current runtime as the source of truth
When the PRD conflicts with code, tests, and active specs, update the PRD to match the implemented contract.

### Keep future ideas clearly labeled or remove them
Aspirational source types or config surface are acceptable only if they are explicitly identified as future possibilities rather than current supported behavior.

### Focus on the highest-risk drift
At minimum, correct:

- `TemplateReference` field names and supported contract
- supported source kinds
- stale mentions of `merge_strategy` as an active source-entry capability

## Implementation Outline

1. Audit the PRD and any remaining secondary docs for stale current-tense contract claims.
2. Update those docs to match the implemented runtime.
3. Run a brief docs sanity pass and OpenSpec status/list checks.

## Risks / Trade-offs

- Over-editing aspirational product text could remove useful future context; keep future ideas only when clearly labeled as non-runtime.
- This change should not spill into runtime code or archived artifacts.
