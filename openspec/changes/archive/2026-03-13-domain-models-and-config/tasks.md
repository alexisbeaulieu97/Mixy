## 1. Domain Models

- [x] 1.1 Create `mixy/domain/models/__init__.py` exporting all models
- [x] 1.2 Implement `VariableDefinition` Pydantic model with type, required, default, description, choices, pattern, secret fields
- [x] 1.3 Implement `SourceDefinition` discriminated union: `LocalDirSource`, `LocalFileSource`, `GitSource` with type field discriminator
- [x] 1.4 Implement `TemplateReference` model with id, source, subpath, alias, enabled, values, merge_strategy fields
- [x] 1.5 Implement `OutputDefinition` model with path and conflict_policy (enum: fail, overwrite, skip)
- [x] 1.6 Implement `ProjectDefinition` model with version, name, description, sources, variables, values, output
- [x] 1.7 Add `ConflictPolicy` enum and `VariableType` enum to `mixy/domain/enums.py`

## 2. Domain Exceptions

- [x] 2.1 Create `mixy/domain/exceptions.py` with base `MixyError` exception
- [x] 2.2 Add `ConfigValidationError` with field_path and suggestion attributes
- [x] 2.3 Add `UnsupportedVersionError` for unknown config versions

## 3. Config Loading

- [x] 3.1 Create `mixy/infrastructure/config/yaml_loader.py` with `load_config(path: Path) -> ProjectDefinition`
- [x] 3.2 Implement version field checking — only version "1" supported, clear error for others
- [x] 3.3 Implement relative path resolution against config file parent directory
- [x] 3.4 Wrap Pydantic validation errors to produce actionable error messages with YAML field paths

## 4. Config Validation Service

- [x] 4.1 Create `mixy/domain/services/config_validator.py` with `validate(definition: ProjectDefinition) -> list[ValidationIssue]`
- [x] 4.2 Implement unique source ID check
- [x] 4.3 Implement variable default type consistency check
- [x] 4.4 Implement choices type consistency check
- [x] 4.5 Implement local source path existence warning

## 5. Tests

- [x] 5.1 Unit tests for each model — valid construction, required fields, default values
- [x] 5.2 Unit tests for source discriminated union — correct dispatch per type, rejection of unknown types
- [x] 5.3 Unit tests for YAML loading — minimal config, full config, missing version, unknown version
- [x] 5.4 Unit tests for relative path resolution
- [x] 5.5 Unit tests for config validator — duplicate IDs, type mismatches, missing paths
- [x] 5.6 Create test fixture YAML files in `tests/fixtures/configs/`
