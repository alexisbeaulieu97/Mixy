## Why

`GenerationExecutor` currently stops on the first filesystem failure, but `GenerationResult` reports very little about what happened before the stop and what operation actually failed. It also folds overwrites into the generic rendered-file count, which hides an operationally important distinction.

This is a reporting problem more than an execution-semantics problem. The bounded fix is to make result reporting more faithful without changing planning or CLI behavior.

## What Changes

- Improve `GenerationResult` to report overwrites and partial failures more explicitly
- Record richer failure information when filesystem execution stops
- Keep the current stop-on-first-write-error behavior unless a spec explicitly changes it
- Add focused tests for execution summaries and partial-failure reporting

## Capabilities

### New Capabilities
- `generation-execution-reporting`: More faithful reporting for overwrites, partial failures, and execution summaries

### Modified Capabilities
- `project-generation-execution`: Filesystem execution reports clearer operational results without changing planning behavior

## Impact

- Refactors `mixy/infrastructure/filesystem/file_writer.py`
- May add one small supporting result dataclass if needed
- Updates generation pipeline tests that assert execution result counts and summaries
