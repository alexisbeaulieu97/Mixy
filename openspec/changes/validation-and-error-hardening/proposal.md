## Why

`mixy validate`, `mixy inspect`, and `mixy generate` still disagree on some invalid-config cases. The clearest example is a missing `local_dir` source path: `validate` reports it as a warning, while `inspect` and `generate` continue into source resolution and then fail later. That makes command behavior harder to predict and delays feedback on generation-blocking config problems.

Coverage is also still thin around `mixy/cli/errors.py`, so several error-formatting branches remain weakly protected even after the recent architecture refactors.

## What Changes

- Promote generation-blocking config issues to fail early during semantic validation
- Align `validate`, `inspect`, and `generate` on exit behavior for those blocking config issues
- Expand focused coverage around CLI error formatting and validation-related command behavior
- Preserve existing non-blocking warnings and command surfaces unless a mismatch is already causing incorrect behavior

## Capabilities

### New Capabilities
- `validation-failure-alignment`: Consistent early failure for generation-blocking config validation issues across commands

### Modified Capabilities
- `project-planning-use-case`: Planning fails earlier for config conditions that are already known to block source materialization
- `cli-error-formatting`: Error and validation output coverage is expanded for user-facing failure cases

## Impact

- Refactors validation severity and/or validation-to-error conversion logic
- Updates CLI tests and error-formatting tests
- Keeps behavior stable except where current command disagreement is already incorrect
