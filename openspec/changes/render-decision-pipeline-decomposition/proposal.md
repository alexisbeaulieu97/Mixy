## Why

`build_render_decisions(...)` in `mixy/application/use_cases/plan_project.py` still combines source metadata discovery, per-file metadata resolution, effective variable context construction, template rendering, and output-path planning in one large function. That concentration makes the planning seam added in the previous change harder to extend and harder to test in smaller units.

## What Changes

- Decompose render-decision planning into smaller application-level helpers with explicit responsibilities
- Keep `prepare_project(...)` and `plan_project(...)` as the stable public planning entry points
- Preserve recursive metadata behavior, path rendering behavior, and render output semantics
- Add focused tests around the decomposed planning helpers and regression coverage for recursive metadata generation

## Capabilities

### New Capabilities
- `render-decision-planning`: Explicit application-level render-decision pipeline stages behind the shared planning use case

### Modified Capabilities
- `project-planning-use-case`: Shared planning flow delegates render-decision work to smaller helpers while preserving output behavior

## Impact

- Refactors `mixy/application/use_cases/plan_project.py`
- May add a narrow helper module under `mixy/application/use_cases/`
- Adds tests that lock in recursive metadata, effective context, and output path planning behavior
