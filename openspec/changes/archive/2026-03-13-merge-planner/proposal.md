## Why

When multiple template sources produce files, they must be merged into a single output directory. This is the most behaviorally critical part of Mixy — surprising merge behavior would destroy user trust. A deterministic merge planner that builds an explicit plan before any writes happen ensures predictability and supports dry-run.

## What Changes

- Implement `MergePlanner` domain service that builds a `RenderPlan` from ordered materialized sources
- Define `FileOperation` value objects: CreateDir, CopyRaw, RenderTemplate, SkipExisting, Overwrite, FailOnConflict
- Implement conflict detection when two sources produce the same output path
- Support three conflict policies: `fail` (default), `overwrite` (later wins), `skip` (earlier wins)
- Directories always merge recursively; file-vs-directory conflicts always fail
- Build deterministic file operation ordering from declared source order

## Capabilities

### New Capabilities
- `merge-planning`: Deterministic merge plan builder with conflict detection, policy enforcement, and ordered file operations

### Modified Capabilities

## Impact

- Creates `mixy/domain/services/merge_planner.py`
- Creates `mixy/domain/models/render_plan.py`
- Creates `mixy/domain/models/file_operation.py`
- Creates `mixy/domain/models/conflict.py`
