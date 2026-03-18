## Why

`TemplateRenderer` now lives in the application layer, but it still imports the raw Jinja rendering helpers and binary-detection logic directly from infrastructure. That leaves the ownership story incomplete: render policy is application logic, while the low-level rendering engine and binary probe are infrastructure concerns. The boundary should be explicit without changing any rendering semantics.

## What Changes

- Introduce the minimal application-owned rendering adapter seam needed by `TemplateRenderer`
- Move default runtime wiring for that seam into composition
- Keep render-policy decisions in the application layer and keep Jinja/binary helpers as infrastructure implementations
- Preserve all current rendering behavior, errors, and path handling

## Capabilities

### New Capabilities
- `renderer-boundary-finalization`: Explicit rendering adapter boundary for application-level template rendering

## Impact

- Refactors internal rendering ownership only
- Preserves CLI behavior, template semantics, and output
- Clarifies that application code owns render policy while infrastructure owns raw rendering mechanics
