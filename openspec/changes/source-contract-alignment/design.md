## Context

The current mismatch is simple: the schema accepts `local_file`, but the runtime has no provider for it and the docs tell users to treat it as unsupported. The cleanest fix is to remove the unsupported type from the contract rather than preserving a dead placeholder in the schema.

## Goals / Non-Goals

**Goals:**
- Make supported source types consistent across schema, runtime, and docs
- Fail fast during config parsing instead of allowing an unsupported source shape deeper into the pipeline
- Keep the change small and independently verifiable

**Non-Goals:**
- Implementing a `local_file` source provider
- Changing provider dispatch semantics for `local_dir` or `git`
- Reworking the overall config-validation architecture

## Decisions

### Remove `local_file` from the schema now
This is intentionally breaking for any config still using `local_file`, but those configs are already non-functional for generation. Removing the dead branch is a smaller and clearer correction than implementing a new provider in this change.

### Align all user-facing messages with the supported set
Runtime suggestions, docs, and fixtures should consistently name `local_dir` and `git` as the supported source types. Any example or fixture still using `local_file` should be updated to expect rejection or be removed if it no longer represents valid input.

## Implementation Outline

1. Remove `LocalFileSource` from the supported source-definition union in the config model.
2. Update path-resolution helpers and unsupported-type suggestions to reference only `local_dir` and `git`.
3. Update README, configuration docs, and any fixtures that still present `local_file` as acceptable input.
4. Add or update tests for source-definition parsing and user-facing failure messaging.

## Risks / Trade-offs

- This is a deliberate contract break, but it removes a non-working configuration path rather than taking away working behavior.
- Any external config depending on `local_file` will now fail earlier and more clearly.
- Some archived design artifacts will still mention `local_file`; those are historical records and do not need to be rewritten.
