## Context

The current source-entry schema exposes more surface area than the runtime actually uses. This change should resolve that drift explicitly rather than allowing configuration fields to exist without trustworthy semantics.

## Goals / Non-Goals

**Goals:**
- Decide and implement the supported semantics for `enabled`, `merge_strategy`, `alias`, and `subpath`
- Keep the public contract honest across models, runtime, docs, and tests
- Keep the change focused on source-entry semantics only

**Non-Goals:**
- Reworking source providers generally
- Redesigning merge planning beyond what `merge_strategy` requires
- Changing unrelated planning architecture

## Decisions

### `enabled` becomes real runtime behavior
`TemplateReference.enabled` stays in the public contract, but `false` now means the source is skipped before resolution, merge planning, and generation.

### Dead contract surface should be rejected, not silently accepted
`merge_strategy` is currently a no-op. This change should make configs fail fast when it is provided instead of preserving a misleading field.

### `alias` remains metadata-only
`alias` is already carried into source metadata. That behavior stays unchanged and should be documented explicitly so callers do not infer merge or path semantics that do not exist.

### `subpath` follows the actual provider boundary
`source.subpath` remains the supported provider-native way to scope both local and git sources. `TemplateReference.subpath` remains supported only as a per-reference override for `local_dir` entries. When used on a git reference, the system should reject it with a clear error instead of ignoring it.

## Implementation Outline

1. Update config validation so `merge_strategy` is rejected and `TemplateReference.subpath` is rejected for non-`local_dir` sources.
2. Update source resolution/planning so disabled sources are filtered before resolution and generation.
3. Preserve `alias` as metadata-only and add focused tests that pin this behavior.
4. Update docs, fixtures, and OpenSpec specs so they match the enforced runtime contract.
5. Run focused tests and the full suite.

## Risks / Trade-offs

- Rejecting `merge_strategy` is intentionally breaking for configs that currently rely on the schema accepting it.
- Enforcing `enabled` changes previously misleading no-op behavior into real filtering, so planning/generation tests need close review.
- The change must keep supported subpath behavior intact for existing `source.subpath` configurations.
