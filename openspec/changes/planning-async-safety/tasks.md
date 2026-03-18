## 1. Planning Concurrency Refactor

- [x] 1.1 Replace the `anyio.run(...)` source-resolution helper in `plan_project.py` with a sync-safe concurrency helper
- [x] 1.2 Preserve input ordering and existing source error behavior for multi-source planning

## 2. Regression Coverage

- [x] 2.1 Add a focused test proving `plan_project(...)` succeeds when called from a running event loop
- [x] 2.2 Keep existing sync planning behavior covered and unchanged

## 3. Validation

- [x] 3.1 Run the focused planning/generation tests affected by the change
- [x] 3.2 Run the full test suite
