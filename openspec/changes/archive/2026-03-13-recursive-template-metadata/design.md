## Context

Recursive metadata turns templates from plain directories into self-describing packages. This is the mechanism that allows a template author to declare "this directory's files should be rendered, except PNGs" or "this file needs a `base_image` variable." The challenge is keeping inheritance rules simple and predictable.

## Goals / Non-Goals

**Goals:**
- Walk a materialized source tree and discover all metadata files
- Build effective metadata for each file by merging scopes from root to leaf
- Validate variable definitions across scopes for compatibility
- Integrate discovered metadata with render policy and variable collection
- Keep inheritance rules strict and narrow — no surprising behavior

**Non-Goals:**
- Metadata for cross-source behavior (merge strategy, cache policy)
- Executable hooks in metadata
- Config imports or template dependencies via metadata
- Metadata schema versioning (inherits from project config version)

## Decisions

### Metadata containers: two forms only
- Directory scope: `.mixy/template.yml` — applies to the directory subtree
- File scope: `<filename>.mixy.yml` — applies to that single file

No other locations are checked. This keeps discovery deterministic and fast.

### Inheritance rules by field type
- **Scalar** (render.undefined, copy_mode): nearest scope wins
- **List** (exclude, include): inherited union — child adds to parent list. A special `_replace: true` key on the list resets rather than appending.
- **Map** (render, variables): deep merge with child keys overriding parent keys at the leaf level

### Variable refinement, not redefinition
A child scope may:
- Add or update `description`
- Provide a more specific `default`
- Add compatible `examples` metadata

A child scope may NOT:
- Change `type`
- Change `secret` flag
- Add `choices` that conflict with parent's `choices`
- Change `required` from false to true

Violations produce a `MetadataConflictError` during planning.

### Disallowed fields in template metadata
The following fields are rejected if found in `.mixy/template.yml` or sidecar files: `source`, `output`, `cache`, `merge_strategy`, `hooks`, `imports`. This boundary prevents templates from overriding project-level composition behavior.

### Metadata sidecar files are excluded from output
`.mixy/` directories and `*.mixy.yml` sidecar files are automatically excluded from the generated output. They are metadata, not content.

## Risks / Trade-offs

- [Recursive discovery adds a walk per source tree] → Templates are typically small; acceptable overhead
- [Union semantics for lists may accumulate large exclude lists] → `_replace: true` escape hatch handles this
- [Variable refinement rules may confuse template authors] → Fail with clear error messages showing parent vs child definitions
- [Sidecar files clutter the template directory] → The `.mixy/template.yml` form handles most cases; sidecar is for per-file exceptions
