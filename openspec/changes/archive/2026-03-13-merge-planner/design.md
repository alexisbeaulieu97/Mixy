## Context

Merge planning is the core behavioral contract of Mixy. When two sources both produce `README.md`, the user must know exactly what happens. The planner builds a complete plan before any filesystem writes, enabling dry-run previews and deterministic conflict detection.

## Goals / Non-Goals

**Goals:**
- Walk materialized source trees and build a flat list of intended output paths
- Detect path collisions between sources
- Apply conflict policy to produce final file operations
- Support deterministic ordering: sources applied in declared config order
- Produce a RenderPlan that the executor consumes without further decisions

**Non-Goals:**
- Content-aware merging (e.g., merging two YAML files key-by-key)
- Per-file conflict policies (global policy only in MVP)
- Symlink handling
- File permission preservation

## Decisions

### Plan-then-execute model
The planner builds the full RenderPlan before any writes. If any conflicts exist and policy is `fail`, the planner raises an error with all conflicts listed — not just the first one. This lets users fix all issues at once.

### FileOperation as tagged union
FileOperations are modeled as a union of dataclasses: `CreateDir(path)`, `CopyRaw(source, dest)`, `RenderTemplate(source, dest, context)`, `SkipExisting(source, dest, reason)`, `Overwrite(source, dest)`. The executor pattern-matches on operation type. Alternative: single class with an action enum — less type-safe, harder to extend.

### Directory merge is implicit, file conflict is explicit
When two sources both contain `src/`, the directories merge silently (this is expected). When two sources both contain `src/main.py`, this is a conflict that requires policy resolution. File-vs-directory conflicts (one source has `foo` as a file, another as a directory) always fail regardless of policy.

### Conflict detection walks all sources before deciding
The planner first collects all output paths from all sources, then detects all conflicts, then applies policy. This ensures the user sees the complete picture in dry-run mode.

## Risks / Trade-offs

- [Building the full plan in memory for huge template trees] → Acceptable for MVP; templates are typically small
- [Global-only conflict policy limits flexibility] → Per-source or per-path policy can be added later
- [No content merge means users must split templates to avoid conflicts] → This is intentional — explicit is better than magic
