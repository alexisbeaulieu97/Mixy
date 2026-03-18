## Why

Planning and merge planning still rediscover the same source-tree information separately. `plan_project(...)` already computes per-file render decisions and output-relative paths, but `MergePlanner` walks each materialized source tree again to rebuild directory ownership and file-entry data. That duplication adds avoidable filesystem work and spreads ownership for the same planning artifact across both the application and domain layers.

## What Changes

- Introduce one internal planned-artifact shape that captures the file entries and directory ownership needed by merge planning
- Build that artifact once during planning and pass it into merge planning instead of rediscovering source trees in `MergePlanner`
- Preserve current merge ordering, conflict detection, and output behavior
- Add focused regression tests for the unified planning artifact path

## Capabilities

### New Capabilities
- `planning-artifact-unification`: Shared planning artifact reused by application planning and domain merge planning

## Impact

- Refactors the boundary between `plan_project(...)` and `MergePlanner`
- Preserves CLI behavior, config schema, and merge semantics
- Reduces duplicate traversal and clarifies ownership of pre-merge planning data
