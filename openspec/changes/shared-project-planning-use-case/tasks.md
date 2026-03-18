## 1. Shared Planning Use Case

- [x] 1.1 Create `mixy/application/use_cases/plan_project.py` with `PreparedProject`, `PlannedProject`, `prepare_project(...)`, and `plan_project(...)`
- [x] 1.2 Move shared load/validate/resolve/render/plan orchestration out of the CLI command path and into the new use case
- [x] 1.3 Centralize output-definition resolution so `generate` and `inspect` differ only by fallback policy

## 2. Command Integration

- [x] 2.1 Refactor `generate_project(...)` into a thin execution wrapper over the shared planner
- [x] 2.2 Refactor `mixy inspect` to consume the shared planner and the shared provider-registry path
- [x] 2.3 Preserve current human-readable inspect output sections and dry-run output behavior

## 3. Validation

- [x] 3.1 Add focused tests for the shared planning path
- [x] 3.2 Add a test proving `generate` and `inspect` use the same default provider-registry assembly path
- [x] 3.3 Run the relevant test suite and update this task list to reflect completion
