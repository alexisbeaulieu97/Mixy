## 1. Test Hardening

- [x] 1.1 Replace the shell-based local Git repository fixture in `tests/test_git_cache_integration.py`
- [x] 1.2 Keep the Git cache integration test focused on provider/cache behavior rather than shell Git setup

## 2. Contract Alignment

- [x] 2.1 Update docs and spec language that still claims Git on PATH is required
- [x] 2.2 Ensure Git runtime messaging reflects the `pygit2` implementation

## 3. Validation

- [x] 3.1 Run Git-focused tests
- [x] 3.2 Run the full test suite and confirm the environment-sensitive Git failure is resolved
