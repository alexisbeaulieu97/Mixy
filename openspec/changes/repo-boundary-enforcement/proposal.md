## Why

The boundary cleanup change moved ownership into `mixy/application/ports/` and `mixy/application/services/`, but it intentionally left thin compatibility shims in old module locations. Those shims were a safe migration step, but leaving them in place indefinitely makes it easy for the repo to drift back toward the old boundaries.

The remaining cleanup should be lightweight: remove stale internal shims that are no longer needed, add a regression check for banned import paths, and document the intended ownership boundary briefly.

## What Changes

- Remove stale compatibility shims that are no longer used inside the repo
- Add a lightweight boundary test that prevents new imports from the retired shim paths
- Add a short architecture note that points contributors at the canonical application-layer ownership

## Capabilities

### New Capabilities
- `architecture-boundary-guardrails`: Lightweight repo checks that keep application-owned services and ports from drifting back into old paths

### Modified Capabilities
- `application-service-ownership`: The repo treats application-layer service and port modules as the canonical import locations

## Impact

- Deletes or simplifies stale migration shims
- Adds a focused architecture-boundary regression test
- Adds a brief contributor-facing note about canonical ownership paths
