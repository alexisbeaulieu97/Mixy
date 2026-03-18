## Context

The recent planning refactors made `inspect` and `generate` share one preparation path, but they still rely on the semantic validator to decide which config problems should stop execution before source resolution. Right now not every generation-blocking condition is treated as an error, so commands can disagree:

- `validate` reports some invalid states only as warnings
- `inspect` and `generate` can then fail later with a different error type

The best bounded fix is to harden the validator and the CLI error coverage around those already-known blocking conditions.

## Goals / Non-Goals

**Goals:**
- Fail early and consistently for config conditions that definitely block planning/generation
- Keep exit-code and message behavior aligned across `validate`, `inspect`, and `generate`
- Add focused tests for `mixy/cli/errors.py` branches that are still lightly covered

**Non-Goals:**
- Reworking every runtime error path in one change
- Introducing a new diagnostics framework
- Changing CLI flags, command names, or overall output layout
- Broadening validator rules into speculative checks that are not clearly generation-blocking

## Decisions

### Treat missing local source paths as validation errors
A `local_dir` path that does not exist cannot succeed during source materialization. That condition should be treated as a semantic error up front rather than as a warning.

### Keep validation conversion explicit
`prepare_project(...)` already converts validation errors into `ConfigValidationError`. This change should keep that flow explicit and ensure `validate` surfaces the same class of blocking issues with the same exit semantics.

### Expand CLI error coverage through focused tests
The lowest-value risk here is hidden behavior drift in `mixy/cli/errors.py`. Add direct tests for representative formatting and exit-code cases rather than relying only on end-to-end coverage.

## Implementation Outline

1. Update semantic validation so generation-blocking local source path problems are classified as errors.
2. Adjust command or helper behavior as needed so `validate`, `inspect`, and `generate` all fail consistently on those validation errors.
3. Add focused tests for:
   - missing local source path validation behavior
   - aligned command exit behavior on blocking validation issues
   - direct CLI error formatting and exit-code mapping branches
4. Run the focused validation/CLI tests and the full suite, then mark tasks complete.

## Risks / Trade-offs

- Some users may currently rely on a missing local source path being a warning during `validate`, but that behavior is already misleading because generation cannot succeed.
- Over-expanding the validator would blur the line between semantic validation and runtime checks. Keep this change limited to clearly known blocking conditions.
- Error-format coverage can drift into broad snapshot testing if it is not kept focused. Prefer small targeted assertions.
