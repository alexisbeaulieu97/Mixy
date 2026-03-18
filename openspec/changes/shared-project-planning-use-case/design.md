## Context

The most immediate architecture issue is duplicated orchestration between `generate` and `inspect`. Both commands need the same prepared project state: loaded config, validated definition, resolved variables, materialized sources, and render decisions. The only meaningful divergence is what they do after planning: `generate` executes and `inspect` formats the result.

## Goals / Non-Goals

**Goals:**
- Extract a shared application planning seam used by both `generate` and `inspect`
- Keep command output stable
- Ensure both commands use the same default source-provider registry
- Reduce duplicated orchestration without redesigning the full domain layer

**Non-Goals:**
- Reworking merge-planner semantics
- Changing CLI flags or output layout
- Solving the entire render-decision decomposition in this change
- Moving provider and renderer contracts out of the domain layer yet

## Decisions

### Introduce `PreparedProject` and `PlannedProject`
The shared use case will return structured planning state rather than forcing each command to reconstruct intermediate values. `PreparedProject` captures the resolved inputs before merge planning, and `PlannedProject` pairs that state with the resolved output definition and render plan.

### Keep output resolution configurable
`generate` and `inspect` differ only in output fallback behavior. The shared planning use case will therefore accept a fallback output path parameter so `generate` can still require a real output path while `inspect` can continue previewing against `<output>`.

### Keep `generate_project` as the execution wrapper
`generate_project` remains the public application entry point for project generation, but it becomes a thin wrapper around the shared planner and the filesystem executor. This preserves the current import surface for tests and CLI code.

## Implementation Outline

1. Add `mixy/application/use_cases/plan_project.py` with:
   - `PreparedProject`
   - `PlannedProject`
   - `prepare_project(...)`
   - `plan_project(...)`
   - shared output-resolution helper(s)
2. Move shared orchestration helpers from `generate_project.py` into the new module.
3. Update `generate_project(...)` to delegate to `plan_project(...)`.
4. Update `inspect_config(...)` to delegate to `plan_project(...)`.
5. Add focused tests proving both commands share the same provider-registry assembly path and preserve output behavior.

## Risks / Trade-offs

- This introduces one more application module, but that module replaces duplicated command orchestration rather than adding a speculative abstraction.
- The current worktree already includes local edits in related files, so patches must preserve behavior and avoid reverting unrelated changes.
- `build_render_decisions` will still be large after this change; deeper decomposition is deferred to the next bounded change.
