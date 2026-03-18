## Context

Mixy's planning seam now owns config loading, variable resolution, source resolution, metadata application, and render decisions. Even after the earlier cleanup work, one major inefficiency remains: `MergePlanner` still walks the materialized source trees again to discover directories and file entries that planning could already know when it builds render decisions.

Today the duplication looks like this:

1. `plan_project(...)` discovers source files and builds `RenderedFile` decisions.
2. `MergePlanner._collect_all(...)` walks the same source roots again to reconstruct directory ownership and per-file output entries.

That split makes the artifact boundary fuzzy. This change should make planning produce one reusable pre-merge artifact and make `MergePlanner` consume it directly.

## Goals / Non-Goals

**Goals:**
- Build the pre-merge artifact once during planning
- Preserve current merge ordering, conflict detection, and operation output
- Keep the public planning and generation use cases stable
- Improve cohesion between planning and merge planning without redesigning domain semantics

**Non-Goals:**
- Changing conflict-policy rules
- Redesigning render decisions or metadata behavior
- Turning `MergePlanner` into an application service

## Decisions

### Add one shared internal planning artifact
Introduce a single internal artifact, likely centered around the existing `PlannedEntry` concept, that contains:

- file entries in source order
- output paths already resolved from render decisions
- directory ownership needed for file-vs-directory conflict checks

The exact type location is an implementation detail, but it should be shared by planning and merge planning instead of rebuilt twice.

### Planning owns collection, merge planner owns conflict policy
The application planning seam should collect directory and file-entry inputs once. `MergePlanner` should continue to own conflict detection, conflict-policy handling, and filesystem operation construction.

### Keep behavior fully stable
No user-visible behavior should change. The same conflicts, operations, overwrite/skip decisions, and output paths must be preserved.

## Implementation Outline

1. Extract the duplicated pre-merge collection into a shared internal artifact produced by planning.
2. Refactor `MergePlanner` to consume that artifact instead of traversing source roots itself.
3. Keep `RenderDecisionMap` behavior stable; this change should not redesign render-decision semantics.
4. Add focused tests proving the unified artifact path preserves:
   - source order
   - file conflict detection
   - file-vs-directory conflict detection
   - operation output paths
5. Run focused planning/merge tests and the full suite.

## Risks / Trade-offs

- The main risk is moving too much logic out of `MergePlanner`. Keep conflict-policy logic in the domain service.
- The shared artifact should stay internal. Avoid turning it into a broad public API.
- Because the current tests already pin merge behavior strongly, the implementation should lean on behavior-preserving refactoring rather than new semantics.
