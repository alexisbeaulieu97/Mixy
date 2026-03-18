## 1. Generation Executor

- [x] 1.1 Create `mixy/infrastructure/filesystem/file_writer.py` with `GenerationExecutor` class
- [x] 1.2 Implement `execute(plan: RenderPlan) -> GenerationResult` that processes each FileOperation
- [x] 1.3 Implement CreateDir operation — create directory with parents
- [x] 1.4 Implement CopyRaw operation — copy file without rendering
- [x] 1.5 Implement RenderTemplate operation — render through Jinja2 and write
- [x] 1.6 Implement Overwrite operation — write over existing file
- [x] 1.7 Create `GenerationResult` dataclass with success/failure counts and file lists

## 2. Generate Project Use Case

- [x] 2.1 Create `mixy/application/use_cases/generate_project.py` with `generate_project` function
- [x] 2.2 Implement pipeline orchestration: load → validate → resolve vars → resolve sources → plan → execute
- [x] 2.3 Accept parameters: config_path, output_override, var_overrides, vars_file, non_interactive, dry_run
- [x] 2.4 Wire dependency injection — construct real implementations of all services

## 3. Dry-Run Support

- [x] 3.1 Implement dry-run mode that builds plan but skips execution
- [x] 3.2 Implement plan display as formatted table (action, output path, source)
- [x] 3.3 Show conflicts in dry-run output if any exist

## 4. Summary Output

- [x] 4.1 Implement generation summary formatting (counts table)
- [x] 4.2 Print summary to stdout after successful generation
- [x] 4.3 Include output path in summary

## 5. Tests

- [x] 5.1 Integration test: generate from local source end-to-end — verify output files exist with correct content
- [x] 5.2 Integration test: dry-run produces plan output without creating files
- [x] 5.3 Integration test: pipeline fails before writes on config error
- [x] 5.4 Integration test: pipeline fails before writes on merge conflict
- [x] 5.5 Unit test: GenerationExecutor processes each operation type correctly
- [x] 5.6 Unit test: GenerationResult counts are accurate
- [x] 5.7 Create end-to-end test fixtures in `tests/fixtures/e2e/`
