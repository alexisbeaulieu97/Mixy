## Context

This is the application layer that ties together all domain services. The pipeline must be linear and predictable: no writes happen until the entire plan is validated. This enables dry-run and ensures that errors are surfaced before any filesystem mutation.

## Goals / Non-Goals

**Goals:**
- Orchestrate: load → validate → resolve vars → resolve sources → plan → execute
- Support dry-run that shows the plan as a table/tree
- Write files atomically per-operation (not whole-project atomic)
- Report a summary with counts: directories created, files rendered, files copied raw, files skipped
- Accept output path override from CLI

**Non-Goals:**
- Whole-project atomic writes (temp dir + rename)
- Rollback on partial failure
- Parallel file writing
- Watch mode or incremental regeneration

## Decisions

### Pipeline as a single function with dependency injection
`generate_project` is a function, not a class. It receives its dependencies (config loader, resolver, planner, executor) as parameters. This makes testing trivial — inject mocks for any stage. The CLI command constructs real implementations and calls the function.

### Executor writes per-operation, not per-plan
Each FileOperation is executed independently. If operation 50 of 100 fails, the first 49 are already written. The executor returns a result summary listing successes and failures. Alternative: write to a temp dir and move — adds complexity without clear benefit for a project generator.

### Dry-run displays a table of planned operations
In dry-run mode, the plan is formatted as a table: `[action] [output path] [source]`. This gives users a clear preview. The table is printed to stdout; logs go to stderr.

### Summary as structured data
The generation summary is a dataclass with counts and lists that can be printed as a table or returned programmatically. This supports future JSON output mode.

## Risks / Trade-offs

- [Per-operation writes leave partial state on failure] → Acceptable for a project generator; user can delete output and retry
- [No parallel writes] → Templates are small; sequential is simpler and deterministic
- [Pipeline function with many parameters] → Use a context/config object if it grows beyond 5-6 params
