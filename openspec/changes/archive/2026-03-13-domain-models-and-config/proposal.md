## Why

Mixy needs a well-defined configuration schema and domain model before any runtime behavior can be built. Every downstream feature — source resolution, variable handling, merge planning — depends on a shared data model that is validated early and fails predictably on malformed input.

## What Changes

- Define Pydantic v2 models for the project configuration schema: ProjectDefinition, TemplateReference, SourceDefinition (discriminated union), VariableDefinition, OutputDefinition
- Implement YAML config loading that deserializes into validated Pydantic models
- Implement a ConfigValidator domain service for semantic validation beyond schema (e.g., unique source IDs, valid variable references)
- Define domain exceptions for config errors with actionable messages
- Support config schema versioning via a `version` field

## Capabilities

### New Capabilities
- `config-schema`: YAML project configuration schema with Pydantic validation, versioning, and typed source/variable definitions
- `config-validation`: Semantic validation of project configuration beyond schema — uniqueness checks, reference integrity, constraint verification

### Modified Capabilities

## Impact

- Creates `mixy/domain/models/` with all core model files
- Creates `mixy/domain/exceptions.py`
- Creates `mixy/domain/services/config_validator.py`
- Creates `mixy/infrastructure/config/yaml_loader.py`
- Extensive unit test coverage for model validation and config loading
