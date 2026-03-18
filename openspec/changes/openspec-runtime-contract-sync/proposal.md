## Why

Several active OpenSpec specs and docs no longer match the current runtime. Examples include `local_file` still appearing in the config schema spec and the Git spec still describing a shell `git` requirement. That makes the planning artifacts unsafe as a source of truth for future changes.

## What Changes

- Audit active OpenSpec specs and user docs against the current runtime
- Correct mismatches in specs, docs, and capability descriptions
- Archive completed change artifacts cleanly where appropriate

## Capabilities

### New Capabilities
- `runtime-contract-sync`: Active OpenSpec/runtime contract alignment for Mixy

## Impact

- Improves trustworthiness of active specs and docs
- Does not intentionally change runtime behavior
