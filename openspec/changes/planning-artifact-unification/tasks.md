## 1. Shared Artifact Extraction

- [x] 1.1 Introduce one internal pre-merge planning artifact that captures file entries and directory ownership
- [x] 1.2 Build that artifact once during planning instead of rediscovering the source tree inside `MergePlanner`

## 2. Merge Planner Refactor

- [x] 2.1 Refactor `MergePlanner` to consume the shared artifact while preserving conflict detection and operation output
- [x] 2.2 Keep source ordering and output-path behavior unchanged

## 3. Validation

- [x] 3.1 Add or update focused planning/merge tests for the unified artifact path
- [x] 3.2 Run the focused affected tests
- [x] 3.3 Run the full test suite
