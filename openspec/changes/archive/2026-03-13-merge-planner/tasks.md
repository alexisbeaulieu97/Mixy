## 1. Domain Models

- [x] 1.1 Create `mixy/domain/models/file_operation.py` with tagged union: CreateDir, CopyRaw, RenderTemplate, SkipExisting, Overwrite
- [x] 1.2 Create `mixy/domain/models/conflict.py` with Conflict dataclass (path, source_a_id, source_b_id, type)
- [x] 1.3 Create `mixy/domain/models/render_plan.py` with RenderPlan (operations, conflicts, conflict_policy, output_path)
- [x] 1.4 Add `MergeConflictError` to domain exceptions

## 2. Merge Planner Service

- [x] 2.1 Create `mixy/domain/services/merge_planner.py` with `MergePlanner` class
- [x] 2.2 Implement source tree walking — collect all file paths from each materialized source
- [x] 2.3 Implement output path mapping — source-relative paths to output-absolute paths
- [x] 2.4 Implement conflict detection — compare output paths across all sources
- [x] 2.5 Implement file-vs-directory conflict detection
- [x] 2.6 Implement conflict policy application (fail, overwrite, skip)
- [x] 2.7 Implement `build_plan(sources: list[MaterializedSource], output: OutputDefinition, render_decisions: dict) -> RenderPlan`

## 3. Tests

- [x] 3.1 Unit test: single source, no conflicts — all files become operations
- [x] 3.2 Unit test: two sources, no conflicts — merged operations
- [x] 3.3 Unit test: two sources, file conflict with fail policy — error with all conflicts
- [x] 3.4 Unit test: two sources, file conflict with overwrite policy — later wins
- [x] 3.5 Unit test: two sources, file conflict with skip policy — earlier wins
- [x] 3.6 Unit test: file-vs-directory conflict — always fails
- [x] 3.7 Unit test: recursive directory merging
- [x] 3.8 Unit test: RenderPlan inspection — list all output paths
- [x] 3.9 Create test fixtures with overlapping source directories in `tests/fixtures/merge/`
