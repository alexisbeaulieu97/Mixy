## 1. Source Provider Protocol

- [x] 1.1 Create `mixy/infrastructure/sources/base.py` with `SourceProvider` Protocol defining `can_handle`, `resolve`, `fingerprint`
- [x] 1.2 Create `mixy/domain/models/materialized_source.py` with `MaterializedSource` dataclass (root_path, source_id, fingerprint, metadata)
- [x] 1.3 Add `SourceResolutionError` to `mixy/domain/exceptions.py`

## 2. Source Resolver Service

- [x] 2.1 Create `mixy/domain/services/source_resolver.py` with `SourceResolver` class
- [x] 2.2 Implement provider registry (register, list providers)
- [x] 2.3 Implement `resolve(source: SourceDefinition) -> MaterializedSource` with provider dispatch
- [x] 2.4 Implement `resolve_all(sources: list[TemplateReference]) -> list[MaterializedSource]` convenience method

## 3. Local Directory Provider

- [x] 3.1 Create `mixy/infrastructure/sources/local.py` with `LocalDirProvider`
- [x] 3.2 Implement `can_handle` — returns True for `local_dir` type
- [x] 3.3 Implement `resolve` — validate path exists, is directory, resolve subpath, return MaterializedSource
- [x] 3.4 Implement `fingerprint` — hash of absolute path + mtime

## 4. Tests

- [x] 4.1 Unit test SourceResolver dispatch — correct provider selected, error on no match
- [x] 4.2 Unit test LocalDirProvider — existing dir, missing dir, file-not-dir, subpath handling
- [x] 4.3 Unit test fingerprint stability
- [x] 4.4 Contract test — verify LocalDirProvider satisfies SourceProvider protocol
- [x] 4.5 Create test fixture directories in `tests/fixtures/sources/`
