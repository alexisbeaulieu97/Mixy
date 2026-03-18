## Context

The previous change corrected ownership but kept thin shims at old import paths to reduce migration risk. The repo has now been updated to the new application-layer imports, so the remaining risk is drift: future edits could quietly reintroduce the old paths unless the repo enforces the new boundaries.

This final cleanup should remain narrow and mechanical.

## Goals / Non-Goals

**Goals:**
- Remove stale shim paths that are no longer used internally
- Add a lightweight automated check that fails if banned legacy import paths reappear
- Document the canonical ownership location for application services and ports

**Non-Goals:**
- Building a full architecture linter
- Restructuring more packages
- Adding runtime behavior changes
- Reopening the earlier application-ownership refactor

## Decisions

### Retire legacy shim paths inside the repo
If the repo no longer imports the temporary shim modules, they should be removed rather than preserved indefinitely.

### Use one focused test instead of a heavy toolchain change
A simple test that scans project Python sources for banned import paths is enough for this repo. It keeps the guardrail visible and cheap without introducing new tooling.

### Keep documentation brief
One short architecture note in existing docs is sufficient. The goal is to point contributors to the canonical paths, not to create a large architecture manual.

## Implementation Outline

1. Remove the now-unused shim modules or shim exports introduced for migration safety.
2. Add a focused test file that fails if repo sources import retired paths such as:
   - `mixy.domain.services.source_resolver`
   - `mixy.domain.services.template_renderer`
   - `mixy.infrastructure.sources.base`
3. Add a short contributor-facing note describing the canonical application-layer ownership for source-provider contracts and impure planning services.
4. Run the focused boundary tests and the full suite, then mark tasks complete.

## Risks / Trade-offs

- Removing shim paths may break external consumers that imported internal modules directly. That is acceptable for this repo-boundary enforcement step as long as internal code is already migrated.
- The boundary test should stay narrow and avoid false positives from unrelated strings or comments where possible.
- Documentation should stay brief; over-documenting would add maintenance cost without much value.
