## Context

Mixy's architecture already moved the major orchestration services into the application layer, but the default runtime wiring is still split across application modules and direct infrastructure imports. The remaining leaks are concrete:

- `plan_project.py` imports `load_config`, `load_vars_file`, and `MetadataLoader`
- `generate_project.py` and `validate_project.py` still default to infrastructure config loaders
- `VariableResolutionService` defaults to `TyperPromptGateway` and `configure_secret_masking(...)`
- `composition.py` imports `get_source_providers()` directly instead of depending on an application-owned provider-registry contract

This change should finish that seam without broadening into renderer redesign or CLI changes.

## Goals / Non-Goals

**Goals:**
- Add only the missing application-owned ports that remove direct infrastructure defaults from application code
- Centralize default runtime wiring in `mixy/application/composition.py`
- Keep public use-case signatures and CLI behavior stable
- Preserve the current runtime implementations as the default adapters

**Non-Goals:**
- Redesigning template rendering boundaries
- Changing config schema, variable semantics, or provider behavior
- Reworking the plugin system beyond wrapping discovery behind a narrow registry interface

## Decisions

### Add only concrete-value ports
This change introduces the minimum additional application-owned contracts needed to complete the current architecture:

- `ConfigLoader`
- `VarsFileLoader`
- `MetadataDiscoverer`
- `SourceProviderRegistry`
- `SecretMasker`

No broader service layer or speculative abstractions should be added.

### Composition owns the default runtime wiring
`mixy/application/composition.py` becomes the single default assembly point for planning/generation concerns. Application modules may still accept injected collaborators, but they should stop importing infrastructure implementations directly for their defaults.

### Preserve existing adapter behavior
Infrastructure loaders, metadata discovery, plugin provider discovery, Typer prompting, and Loguru masking remain the default runtime behavior. This change is about ownership and dependency flow, not behavior.

## Implementation Outline

1. Add the missing ports under `mixy/application/ports/`:
   - config loader callable
   - vars file loader callable
   - metadata discovery contract
   - source provider registry contract
   - secret masker contract
2. Extend `mixy/application/composition.py` with default builders for:
   - planning loaders and metadata discovery
   - source provider registry / provider list resolution
   - prompt gateway and secret masker used by `VariableResolutionService`
3. Refactor `plan_project.py`, `generate_project.py`, and `validate_project.py` to use composition-owned defaults instead of direct infrastructure imports.
4. Refactor `VariableResolutionService` so the Typer prompt adapter and Loguru masker are injected defaults assembled by composition.
5. Add or update focused tests covering composition and behavior preservation, then run the full suite.

## Risks / Trade-offs

- The main risk is over-design. The new contracts should stay small and specific to the existing default runtime needs.
- This change touches dependency assembly, so it can accidentally widen if it starts redesigning rendering or execution; keep those concerns out of scope.
- Some application modules currently use callable type aliases instead of explicit protocols. The implementation can keep that style where it remains the simplest option.
