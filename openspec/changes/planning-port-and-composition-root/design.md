## Context

The previous changes clarified ownership, but planning and generation still create concrete collaborators inline. This change should move dependency assembly into one explicit place without redesigning the use cases themselves.

## Goals / Non-Goals

**Goals:**
- Introduce narrow application ports where planning/generation still depend on concrete adapters
- Centralize default runtime wiring in a composition root
- Preserve current CLI and use-case behavior

**Non-Goals:**
- Rewriting use-case logic
- Redesigning provider discovery or template rendering semantics
- Changing user-facing command behavior

## Decisions

### Keep the composition root small
This change should assemble defaults, not become a new service layer.

### Add only ports with concrete value
Do not create speculative interfaces. Introduce only the seams needed to stop hardwiring concrete adapters in planning/generation.

## Implementation Outline

1. Audit concrete dependencies created inside planning/generation use cases.
2. Define the minimum new application ports required.
3. Add a default composition module that wires runtime adapters.
4. Update use cases and CLI entrypoints to consume the composition path.

## Risks / Trade-offs

- Over-design is the main risk. The port surface should stay minimal.
- This change depends on preceding boundary cleanup so it should not reopen earlier ownership work.
