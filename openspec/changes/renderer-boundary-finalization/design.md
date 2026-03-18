## Context

The earlier layer-boundary cleanup moved `TemplateRenderer` into `mixy/application/services/`, which correctly identified it as application orchestration. But the service still reaches directly into infrastructure for:

- binary detection
- Jinja string rendering
- Jinja suffix helpers

The remaining issue is not where the service lives, but how it depends on raw rendering mechanics. This change should finish the boundary so the application service owns policy and error mapping while infrastructure provides the rendering primitives.

## Goals / Non-Goals

**Goals:**
- Add the smallest rendering adapter seam that removes direct infrastructure helper imports from `TemplateRenderer`
- Keep render-policy logic and `RenderingError` mapping in the application layer
- Move default adapter wiring into composition
- Preserve all current behavior and tests

**Non-Goals:**
- Changing template syntax or Jinja behavior
- Redesigning copy-mode or include/exclude semantics
- Reworking planning, metadata, or merge behavior

## Decisions

### Keep `TemplateRenderer` as the application policy service
The service should continue to decide:

- whether a file should render
- whether paths should render
- how render-policy include/exclude rules behave
- how low-level failures are mapped into `RenderingError`

### Push raw mechanics behind a narrow adapter
Introduce one small application-owned rendering adapter contract that covers only the mechanics `TemplateRenderer` needs:

- check whether a file is binary
- strip the Jinja suffix from a filename/path segment
- detect whether a path forces rendering because of its suffix
- render a string with context

This keeps the surface small and avoids splitting one cohesive low-level concern into too many mini-ports.

### Composition owns the default adapter
The default Jinja/binary implementation remains the runtime implementation, but only composition should assemble it.

## Implementation Outline

1. Add a minimal application-owned rendering adapter contract.
2. Refactor `TemplateRenderer` to depend on that adapter rather than importing infrastructure helpers directly.
3. Add the default adapter wiring to composition.
4. Update focused renderer/composition tests to prove behavior is unchanged.
5. Run the focused renderer/planning tests and the full suite.

## Risks / Trade-offs

- Over-design is the main risk; one small adapter is enough.
- The service must keep error mapping behavior stable while changing only the dependency source.
- Because rendering is heavily exercised indirectly, focused tests should cover both direct renderer behavior and planning integration.
