## Why

`TemplateReference` exposes fields whose runtime meaning is unclear or currently absent. `enabled` is modeled but not enforced, `merge_strategy` is accepted but ignored, and `alias`/`subpath` semantics are only partially reflected in docs and planning behavior. That leaves the public config contract misleading.

## What Changes

- Define explicit supported semantics for `enabled`, `merge_strategy`, `alias`, and `subpath`
- Align schema, runtime behavior, docs, and tests with those semantics
- Prefer removing dead contract surface over preserving misleading fields

## Decided Contract

- `enabled: false` skips the source entirely during planning and generation.
- `alias` remains supported as metadata only; it does not affect merge order or file paths.
- `merge_strategy` is not supported and should be rejected instead of silently accepted.
- `TemplateReference.subpath` is supported only for `local_dir` references as a per-reference override.
- Git subpaths remain configured only through `source.subpath`; using reference-level `subpath` on a git source should be rejected.

## Capabilities

### New Capabilities
- `source-entry-contract-alignment`: Explicit, documented, and enforced `TemplateReference` field semantics

## Impact

- Intentionally changes currently misleading no-op behavior into explicit enforcement or rejection
- Preserves existing working behavior for supported source configurations
