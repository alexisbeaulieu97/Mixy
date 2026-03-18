## 1. Contract Alignment

- [x] 1.1 Remove `local_file` from the supported source-definition schema
- [x] 1.2 Update source-resolution and schema suggestion text to reference only `local_dir` and `git`
- [x] 1.3 Update path-resolution helpers to match the supported source set

## 2. Docs And Fixtures

- [x] 2.1 Update README and configuration docs to describe `local_dir` and `git` as the supported source types
- [x] 2.2 Update fixtures and tests that still treat `local_file` as accepted input

## 3. Validation

- [x] 3.1 Add regression coverage for rejecting `local_file`
- [x] 3.2 Run the relevant test suite and confirm the failure mode is early and actionable
