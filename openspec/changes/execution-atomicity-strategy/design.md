## Context

Mixy's executor currently reports partial failures accurately, but it does not prevent partial output. Whether that is acceptable depends on the intended reliability contract. This change exists to make that decision explicit before code is changed.

## Goals / Non-Goals

**Goals:**
- Decide and document Mixy's execution guarantees on write failure
- Define the minimum implementation needed for the chosen strategy
- Keep the design separate from unrelated planning or rendering refactors

**Non-Goals:**
- Sneaking in an executor rewrite without a clear contract decision
- Changing merge planning, dry-run behavior, or CLI flags unless required by the chosen strategy

## Decisions

### Preserve partial writes for now
Mixy should keep its current execution model: apply operations in order, stop on the first write failure, and report partial failure details. Already-written output remains on disk and no rollback or cleanup is guaranteed.

### Do not add staging or rollback in phase two
Transactional generation would add meaningful filesystem complexity and a larger behavior change. That does not meet the current bar for an incremental migration step.

### Test and document the failure contract directly
Because the preserved behavior can surprise users, the contract should be pinned in tests and made explicit in active specs/docs.

## Implementation Outline

1. Update active specs/docs to state that generation may leave partial output after a write failure.
2. Add or tighten focused failure-path tests so they explicitly verify:
   - earlier successful writes remain on disk
   - execution stops at the first failing operation
   - later operations are not attempted
   - failure reporting includes the failed target and source context
3. Keep the executor implementation unchanged unless a tiny correction is needed to match the documented contract.

## Risks / Trade-offs

- Users must handle cleanup themselves after a partial failure.
- Stronger guarantees remain a possible future change, but they require a separate product decision and implementation budget.
