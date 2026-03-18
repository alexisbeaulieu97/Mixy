## Context

Planning and generation already run through the application layer, but validation still loads config and invokes domain validation directly from the CLI command. This change closes that remaining gap.

## Goals / Non-Goals

**Goals:**
- Add an application-level validation use case
- Make the CLI command consume that use case
- Preserve output formatting and exit semantics

**Non-Goals:**
- Reworking validation rules themselves
- Changing validation issue formatting
- Broadening the scope into source-entry or planning refactors

## Decisions

### Keep validation output stable
This change is structural. It should not introduce a new diagnostics format.

### Reuse existing validators
The new use case should compose current config loading and semantic validation rather than replacing them.

## Implementation Outline

1. Add `validate_project` in the application layer.
2. Move the CLI `validate` command to use it.
3. Keep `cli/errors.py` and issue formatting unchanged except for any narrow test-driven adjustments.

## Risks / Trade-offs

- Low risk. The main concern is preserving current exit and formatting behavior.
