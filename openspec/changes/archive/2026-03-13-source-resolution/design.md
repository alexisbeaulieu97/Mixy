## Context

Source resolution is the first runtime step after config loading. It transforms abstract source definitions into concrete, local filesystem trees. The abstraction must support local directories now and Git repositories later without changing the consuming code.

## Goals / Non-Goals

**Goals:**
- Define a SourceProvider protocol that all providers implement
- Implement local directory source resolution
- Create a registry-based dispatcher so the resolver doesn't need to know about specific providers
- Return a MaterializedSource that downstream code (renderer, merger) consumes uniformly

**Non-Goals:**
- Git source resolution (separate change)
- Remote archive sources
- Source caching (comes with git-source-and-caching)
- Template metadata discovery within sources (separate change)

## Decisions

### Protocol-based provider contract using Python typing.Protocol
Use `typing.Protocol` for the SourceProvider interface rather than an ABC. This enables structural subtyping — providers don't need to inherit from a base class, just implement the required methods. Alternative: ABC with abstract methods — requires explicit inheritance which couples providers to the base.

### MaterializedSource as a simple value object
MaterializedSource holds: `root_path` (Path to local directory), `source_id` (from config), `fingerprint` (content hash or identifier), and `metadata` (optional dict). It does not hold file listings — the merge planner walks the tree itself. This keeps the object lightweight.

### Provider registry as a simple list with linear dispatch
SourceResolver holds a list of providers and iterates `can_handle` to find the right one. For 2-3 providers this is fine. Alternative: dict keyed by source type string — slightly faster but less flexible for providers that handle multiple types.

### Local directory provider validates existence at resolve time
The provider checks that the directory exists and is readable when `resolve()` is called, not at config load time. This matches the principle that config validation warns but resolution fails hard.

## Risks / Trade-offs

- [Protocol-based interface has no runtime enforcement] → Use unit tests and contract tests to verify provider compliance
- [Local provider is trivial — wrapping a Path in an object may feel like overhead] → The uniformity pays off when Git and future providers join the registry
