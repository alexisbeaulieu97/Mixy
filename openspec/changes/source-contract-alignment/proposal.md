## Why

Mixy currently advertises three source types in some places, implements only two at runtime, and documents the mismatch as a limitation. That leaves users with a configuration shape that parses but cannot be executed, which is a contract bug rather than a missing future enhancement.

## What Changes

- **BREAKING** Remove `local_file` from the supported source-definition contract
- Align schema, runtime error messaging, docs, fixtures, and tests around `local_dir` and `git` as the only supported source types
- Update config-loading path resolution and suggestion text to match the supported source set
- Add regression tests proving unsupported source types fail immediately and consistently

## Capabilities

### New Capabilities

### Modified Capabilities
- `config-schema`: remove `local_file` from the supported source-definition contract
- `source-provider-contract`: narrow provider messaging and unsupported-type guidance to the actual supported provider set

## Impact

- Modifies source-definition models and config-loading path resolution
- Modifies runtime suggestion text in source resolution and schema validation
- Updates README, configuration docs, fixtures, and source-definition tests
- Intentionally breaks configs that still rely on the unsupported `local_file` placeholder
