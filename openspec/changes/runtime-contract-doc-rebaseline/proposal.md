## Why

The runtime architecture queue is now largely implemented, but one documentation mismatch remains: the product PRD and other secondary docs still describe stale or aspirational contract surface as if it were current runtime behavior. Examples include `TemplateReference.merge_strategy`, extra source kinds such as local files or remote archives, and older field names that no longer match the current config model. That drift can mislead future planning even though the active runtime specs are aligned.

## What Changes

- Audit the remaining secondary docs against the current runtime
- Update stale contract descriptions in the PRD and any other secondary docs that still contradict the code
- Keep active runtime specs and archived historical artifacts untouched unless a small clarification is necessary

## Capabilities

### New Capabilities
- `runtime-contract-doc-rebaseline`: Secondary documentation aligned with the current runtime contract

## Impact

- Docs-only change
- Preserves runtime behavior, CLI semantics, and OpenSpec runtime contracts
- Reduces the chance of future work starting from stale assumptions
