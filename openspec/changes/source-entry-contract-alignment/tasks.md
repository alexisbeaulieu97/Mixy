## 1. Contract Audit

- [x] 1.1 Audit runtime behavior for `enabled`, `merge_strategy`, `alias`, and `subpath`
- [x] 1.2 Decide which fields are supported, rejected, or removed

## 2. Alignment

- [x] 2.1 Update code so `enabled=false` skips a source, `merge_strategy` is rejected, and reference-level `subpath` is rejected for non-`local_dir` sources
- [x] 2.2 Update docs, fixtures, and specs to document `alias` as metadata-only and the chosen `subpath` contract

## 3. Validation

- [x] 3.1 Add focused tests for disabled sources, rejected `merge_strategy`, rejected git reference `subpath`, and metadata-only `alias`
- [x] 3.2 Run focused tests and the full suite
