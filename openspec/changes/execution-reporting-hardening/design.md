## Context

The generation pipeline now has better planning structure and boundary ownership, but the execution result is still coarse. In particular:

- overwrites are counted as generic rendered files
- failures only record a path, not the operation context
- summaries do not make partial execution obvious

The executor should still stop on first filesystem failure for now. This change is only about making the reported result accurate enough for users and later refactors.

## Goals / Non-Goals

**Goals:**
- Distinguish overwrites from normal renders in the execution result
- Capture enough context about failed operations to make partial execution understandable
- Make summary output clearly reflect partial execution when a failure occurs
- Preserve current execution control flow

**Non-Goals:**
- Continuing after write failures
- Redesigning the render plan model
- Changing CLI flags or dry-run behavior
- Reworking merge conflict handling

## Decisions

### Preserve stop-on-first-failure semantics
The executor should keep halting on the first `OSError`. This change improves observability, not failure recovery.

### Add explicit overwrite and failure reporting
`GenerationResult` should distinguish normal rendered files from overwritten files and should capture richer failure details than a bare path. A small supporting result dataclass is acceptable if it keeps the structure explicit.

### Keep summary output compact but more truthful
`format_summary()` should remain concise, but it should expose overwrite counts and make partial execution visible when failures occurred.

## Implementation Outline

1. Update `GenerationResult` to track overwritten files separately and to carry structured failure information.
2. Update `GenerationExecutor.execute(...)` to populate the richer result while preserving current execution flow.
3. Update or add focused tests covering:
   - overwrite accounting
   - failed operation details
   - summary output for partial execution
4. Run the focused generation tests and the full suite, then mark tasks complete.

## Risks / Trade-offs

- Changing `GenerationResult` shape could affect existing callers, so preserve the current fields where possible and extend rather than replace.
- Summary wording changes should stay small to avoid brittle tests or unnecessary CLI churn.
- Reporting more detail is useful, but avoid turning the result object into a verbose log dump.
