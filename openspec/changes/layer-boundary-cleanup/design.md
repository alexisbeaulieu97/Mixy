## Context

The previous changes established a shared planning seam and decomposed its largest orchestration hotspot. The next structural issue is ownership: services that coordinate infrastructure-backed behavior still live under `mixy/domain/services/`, which makes the package structure misleading.

Two boundary problems are concrete today:

1. `SourceResolver` is an impure application service, but it lives in `mixy/domain/services/` and depends on the provider protocol defined under `mixy/infrastructure/sources/base.py`.
2. `TemplateRenderer` is also an impure application service, but it lives in `mixy/domain/services/` and directly imports Jinja and binary-detection helpers from infrastructure modules.

This change should correct ownership without widening into a larger renderer redesign.

## Goals / Non-Goals

**Goals:**
- Move `SourceResolver` and `TemplateRenderer` into the application layer
- Move the `SourceProvider` protocol into `mixy/application/ports/`
- Update internal imports so the planning flow and plugin manager depend on application-owned contracts
- Preserve existing resolver and renderer behavior

**Non-Goals:**
- Redesigning template rendering semantics
- Reworking the pluggy extension mechanism
- Changing CLI behavior or output
- Removing all compatibility shims for old import paths if a thin shim is the safest migration step

## Decisions

### Application layer owns orchestration-facing services
`SourceResolver` and `TemplateRenderer` should move to `mixy/application/services/`. They are not pure domain policy and they are used by application use cases to coordinate infrastructure-backed behavior.

### Application layer owns the provider contract
`SourceProvider` should move to `mixy/application/ports/`. Infrastructure providers and plugin hooks should implement or reference that application-level contract rather than defining the contract inside infrastructure.

### Prefer an incremental migration over a hard import break
If removing the old import paths would create unnecessary churn or external breakage, thin compatibility re-exports are acceptable as part of this bounded change. The important requirement is that new ownership is clear and all internal application code uses it.

## Implementation Outline

1. Add application-layer modules for:
   - `SourceProvider` protocol
   - `SourceResolver`
   - `TemplateRenderer`
2. Update use cases, plugin hooks, provider manager, and internal tests to import from the new application-layer locations.
3. Reduce `mixy/domain/services/__init__.py` to pure services only, or leave only thin compatibility shims if needed for migration safety.
4. Keep provider implementations and renderer helpers in infrastructure as concrete implementations used by the application-layer services.
5. Run the focused resolver, renderer, planning, and plugin-related tests, then the full suite.

## Risks / Trade-offs

- This change touches imports across several modules, so the worker should keep the write scope tightly focused on ownership and not mix in behavioral changes.
- A hard removal of legacy import paths could create unnecessary breakage. Thin shims are acceptable if they keep the change safer.
- Introducing too many new abstraction types would be over-design. One provider protocol and a straightforward move of the two services is sufficient.
