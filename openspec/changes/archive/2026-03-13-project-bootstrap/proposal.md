## Why

Mixy has no runnable codebase yet. Before any domain logic can be implemented, the project needs a Python package with dependency management, a CLI entry point, and a test harness. This is the foundation every subsequent change builds on.

## What Changes

- Initialize a Python 3.11+ project with pyproject.toml using uv as the package manager
- Create the layered package structure: `mixy/cli/`, `mixy/domain/`, `mixy/application/`, `mixy/infrastructure/`
- Add core dependencies: typer[all], jinja2, pyyaml, pydantic >= 2.0, loguru, platformdirs
- Add dev dependencies: pytest, pytest-cov, ruff, mypy
- Create a minimal Typer CLI app with a `mixy version` command
- Set up pytest configuration and a passing smoke test

## Capabilities

### New Capabilities
- `cli-entry-point`: Typer-based CLI app with version command and global options skeleton
- `package-structure`: Python package layout with layered architecture directories and build configuration

### Modified Capabilities

## Impact

- Creates the entire `mixy/` package from scratch
- Establishes pyproject.toml with all build and tool configuration
- Sets up `tests/` directory with pytest infrastructure
