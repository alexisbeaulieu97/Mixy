## Context

The domain `VariableResolver` currently mixes pure policy with interface/runtime side effects. It imports Typer for prompting, stores prompt state internally, and configures Loguru masking globally. Those behaviors work, but they are architectural leaks.

This change should make the domain resolver responsible only for precedence selection, coercion, and validation. Prompt orchestration and log masking should move outward without widening into the later composition-root change.

## Goals / Non-Goals

**Goals:**
- Remove Typer prompting from the domain resolver
- Remove Loguru masking side effects from the domain resolver
- Preserve current variable precedence, prompt behavior, and secret masking behavior for CLI-driven planning/generation
- Keep the public use-case APIs stable unless a narrow dependency parameter must be added for testing

**Non-Goals:**
- Redesigning variable precedence or validation rules
- Reworking all application dependency assembly in this change
- Changing CLI options or user-facing prompt wording beyond what is required to preserve current behavior
- Solving unrelated source-entry contract drift

## Decisions

### Domain resolver becomes pure and stateless with respect to prompting
`VariableResolver` should no longer own a prompt function or a mutable prompt cache. Missing required variables will surface as `VariableResolutionError`, and the application-owned variable-resolution service will decide whether to prompt and retry.

### Application layer owns interactive resolution
A new application service will wrap `VariableResolver`, maintain prompt cache across planning steps, and use a `PromptGateway` to request missing values only when interactive behavior is allowed.

### Secret masking moves to infrastructure logging
Secret-value masking remains part of runtime behavior, but it should live in an infrastructure logging helper that the application service invokes after successful resolution.

## Implementation Outline

1. Refactor `mixy/domain/services/variable_resolver.py` so it only performs precedence selection, coercion, and validation.
2. Add an application-owned variable-resolution service plus a `PromptGateway` port.
3. Add an infrastructure helper for Loguru secret masking and wire it through the application service.
4. Update `plan_project` to use the application-owned variable-resolution service for global resolution and per-file effective contexts.
5. Update tests:
   - keep domain resolver tests focused on pure resolution behavior
   - move prompting and secret-masking coverage to application/integration tests
   - run focused tests and the full suite

## Risks / Trade-offs

- Prompt orchestration changes can drift subtly if the prompt cache is not preserved across planning stages.
- Secret masking is global Loguru state, so tests need careful isolation.
- This change should stop at the variable-resolution seam and avoid expanding into a broader composition-root redesign.
