## Context

The config schema is the contract between the user (YAML file) and every internal subsystem. Getting it wrong forces painful migrations later. The schema must be strict enough to catch errors early but flexible enough for future extension.

## Goals / Non-Goals

**Goals:**
- Define all MVP domain models as Pydantic v2 BaseModel subclasses
- Support discriminated union for SourceDefinition (local_dir, local_file, git)
- Load and validate YAML config files in a single call
- Provide clear, actionable error messages for invalid configs
- Support schema versioning for future evolution

**Non-Goals:**
- Config file generation or scaffolding
- Config composition/imports
- Template-local metadata (handled in recursive-template-metadata change)
- Runtime variable resolution (separate change)

## Decisions

### Pydantic discriminated unions for SourceDefinition
Use Pydantic's `Discriminator` on the `type` field to route to LocalDirSource, LocalFileSource, or GitSource models. This gives automatic validation per source type and clear error messages. Alternative: manual dispatch with if/elif — loses type safety and validation.

### Config version as string, not int
`version: "1"` as a string allows semver-style versioning later if needed. The loader checks the version field and dispatches to the appropriate parser. For MVP, only version "1" is supported.

### Flat variable namespace with per-source overrides
Variables are declared globally in `variables:` and values supplied in `values:`. Per-source `values:` override globals for that source only. No nested variable objects in MVP. Alternative: namespaced variables like `base.project_name` — adds complexity without clear benefit for MVP.

### Semantic validation as a separate pass
Schema validation (Pydantic) catches structural errors. A ConfigValidator service runs after parsing to check semantic rules: unique source IDs, no circular references, variable types match declared constraints. This separation keeps the models clean.

### Config file path resolution
All relative paths in config (source paths, output path) are resolved relative to the config file's parent directory, not the current working directory. This makes configs portable.

## Risks / Trade-offs

- [Pydantic v2 discriminated unions have subtle serialization edge cases] → Test round-trip serialization; keep models simple
- [Strict schema may reject valid-looking configs] → Provide example configs in error messages and docs
- [Version field creates forward-compatibility pressure] → Only support version "1" in MVP; reject unknown versions with a clear message
