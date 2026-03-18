## 1. Metadata Models

- [x] 1.1 Create `mixy/domain/models/template_metadata.py` with `TemplateMetadata` Pydantic model
- [x] 1.2 Define allowed fields: variables, defaults, render, include, exclude, copy_mode, description
- [x] 1.3 Implement validation that rejects disallowed fields (source, output, cache, etc.)
- [x] 1.4 Add `MetadataConflictError` and `MetadataValidationError` to domain exceptions

## 2. Metadata Loader

- [x] 2.1 Create `mixy/infrastructure/config/metadata_loader.py`
- [x] 2.2 Implement `.mixy/template.yml` discovery — walk source tree directories
- [x] 2.3 Implement `<filename>.mixy.yml` sidecar discovery — scan for adjacent sidecar files
- [x] 2.4 Parse discovered metadata files into `TemplateMetadata` models

## 3. Metadata Resolver Service

- [x] 3.1 Create `mixy/domain/services/metadata_resolver.py` with `MetadataResolver` class
- [x] 3.2 Implement scope hierarchy builder — project → root → nested dirs → file, ordered by specificity
- [x] 3.3 Implement scalar inheritance — nearest scope wins
- [x] 3.4 Implement list inheritance — union with `_replace` escape hatch
- [x] 3.5 Implement map inheritance — deep merge with child override
- [x] 3.6 Implement variable refinement validation — check type, secret, choices compatibility
- [x] 3.7 Implement `resolve_for_file(file_path: Path, source_root: Path, project_defaults: TemplateMetadata) -> EffectiveMetadata`

## 4. Integration

- [x] 4.1 Add metadata file exclusion to merge planner — skip `.mixy/` and `*.mixy.yml` from output
- [x] 4.2 Integrate effective metadata with template renderer render policy
- [x] 4.3 Integrate discovered variable definitions with variable resolver

## 5. Tests

- [x] 5.1 Unit test metadata model — valid fields, rejected disallowed fields
- [x] 5.2 Unit test discovery — directory scope, file sidecar, no metadata
- [x] 5.3 Unit test scalar inheritance — nearest scope wins
- [x] 5.4 Unit test list inheritance — union and replace
- [x] 5.5 Unit test map inheritance — deep merge
- [x] 5.6 Unit test variable refinement — valid refinement, type change rejection, choice conflict
- [x] 5.7 Integration test: full source tree with nested metadata, verify effective metadata per file
- [x] 5.8 Integration test: metadata files excluded from output
- [x] 5.9 Create test fixture source trees with metadata in `tests/fixtures/metadata/`
