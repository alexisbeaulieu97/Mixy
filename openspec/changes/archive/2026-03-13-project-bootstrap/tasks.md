## 1. Project Configuration

- [x] 1.1 Create pyproject.toml with uv-compatible build system, Python >= 3.11, project metadata (name, version, description, license)
- [x] 1.2 Add runtime dependencies: typer[all], jinja2, pyyaml, pydantic >= 2.0, loguru, platformdirs
- [x] 1.3 Add dev dependencies: pytest, pytest-cov, ruff, mypy
- [x] 1.4 Configure ruff settings in pyproject.toml (target Python 3.11, line length 100)
- [x] 1.5 Configure mypy settings in pyproject.toml (strict mode)
- [x] 1.6 Configure pytest settings in pyproject.toml (testpaths, coverage)

## 2. Package Structure

- [x] 2.1 Create `mixy/__init__.py` with `__version__` variable
- [x] 2.2 Create `mixy/cli/__init__.py` and `mixy/cli/app.py` with Typer app instance
- [x] 2.3 Create `mixy/domain/__init__.py` (empty, establishes layer)
- [x] 2.4 Create `mixy/application/__init__.py` (empty, establishes layer)
- [x] 2.5 Create `mixy/infrastructure/__init__.py` (empty, establishes layer)
- [x] 2.6 Register `mixy` console script entry point in pyproject.toml pointing to `mixy.cli.app:app`

## 3. CLI Foundation

- [x] 3.1 Implement `mixy version` command that reads version from package metadata
- [x] 3.2 Add `--log-level` global option (debug, info, warning, error) with default "info"
- [x] 3.3 Configure loguru to respect the `--log-level` setting

## 4. Test Infrastructure

- [x] 4.1 Create `tests/__init__.py` and `tests/conftest.py`
- [x] 4.2 Write smoke test that imports mixy and verifies version is a string
- [x] 4.3 Write CLI test using Typer's CliRunner that verifies `mixy version` outputs version
- [x] 4.4 Write CLI test that verifies `mixy --help` returns exit code 0
- [x] 4.5 Verify `uv sync && uv run pytest` passes from clean state
