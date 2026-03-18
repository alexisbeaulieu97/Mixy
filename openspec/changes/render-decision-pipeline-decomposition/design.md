## Context

The shared planning use case is now the correct seam for both `generate` and `inspect`, but its internal render-decision logic is still monolithic. The current `build_render_decisions(...)` function owns five different responsibilities:

1. Discover source metadata files and scopes
2. Resolve effective metadata for each source file
3. Build the effective variable context for that file
4. Render file content with the resolved policy
5. Compute the final output-relative path

This change should decompose that pipeline without redesigning the broader application layer.

## Goals / Non-Goals

**Goals:**
- Split render-decision planning into smaller helpers with one clear responsibility each
- Preserve current recursive metadata and file rendering behavior
- Keep the public planning API stable for `generate` and `inspect`
- Improve testability around source-level planning and per-file decision assembly

**Non-Goals:**
- Changing merge-plan semantics
- Moving renderer or metadata services out of their current packages
- Altering CLI output, dry-run output, or conflict handling
- Expanding into the later layer-boundary cleanup change

## Decisions

### Keep decomposition inside the application layer
The new helpers stay under `mixy/application/use_cases/` because this change is about orchestration structure, not domain ownership. This keeps the write scope narrow and avoids mixing it with the separate boundary-cleanup change.

### Extract source-level and file-level planning steps
The implementation should split the current logic into explicit stages:

- source metadata discovery and source-file enumeration
- per-file effective metadata and effective context resolution
- rendered-file decision assembly, including output-relative path planning

Whether these stages live as private helpers in `plan_project.py` or in one small adjacent helper module is an implementation detail. The important constraint is that each stage is independently readable and testable.

### Preserve the current `RenderDecisionMap` contract
`prepare_project(...)`, `plan_project(...)`, and downstream merge planning should continue to consume the same `RenderDecisionMap` shape. No external caller should need to change.

## Implementation Outline

1. Refactor `build_render_decisions(...)` so it delegates to smaller helpers for:
   - discovering per-source metadata context
   - building per-file effective context
   - assembling `RenderedFile` decisions
2. Keep `_render_output_relative_path(...)` behavior stable, but move it next to the file-decision assembly logic if that improves cohesion.
3. Add or update focused tests covering:
   - recursive metadata application
   - path rendering decisions
   - preservation of rendered content and output-relative paths
4. Update the task list after the focused validation suite passes.

## Risks / Trade-offs

- Introducing too many helper types would turn a straightforward refactor into speculative architecture. Keep the new surface minimal.
- The relevant code sits on a hot orchestration path, so the tests need to prove behavior preservation rather than only structural decomposition.
- The repo is already mid-migration, so the worker should avoid widening the change into provider, validator, or executor concerns.
