## Context

Mixy is a greenfield Python CLI project. There is no existing codebase beyond documentation. The project needs a clean foundation that supports a layered architecture (domain, application, infrastructure, CLI) without over-engineering the initial setup.

## Goals / Non-Goals

**Goals:**
- Establish a buildable, installable Python package
- Create directory structure that enforces layer boundaries
- Provide a working CLI entry point via Typer
- Set up linting (ruff), type checking (mypy), and testing (pytest)
- Pin Python >= 3.11 for modern syntax support (match statements, tomllib, etc.)

**Non-Goals:**
- Implementing any domain logic
- Creating CI/CD pipelines
- Publishing to PyPI
- Configuring Docker or container builds

## Decisions

### Package manager: uv
uv provides fast dependency resolution, virtual environment management, and is compatible with standard pyproject.toml. It is significantly faster than pip and Poetry for dependency operations. Alternative considered: Poetry — slower, heavier, uv is the chosen tool for this project.

### CLI framework: Typer
Typer provides type-hint-driven argument parsing, auto-generated help, and supports subcommand groups needed for `mixy cache list/clear`. Alternative considered: Click — Typer is built on Click but reduces boilerplate. Alternative considered: argparse — too verbose for nested subcommands.

### Package layout: src-less flat layout
Use `mixy/` at repo root rather than `src/mixy/`. This is simpler and sufficient for a CLI tool that won't be published as a library. The layered subdirectories (`cli/`, `domain/`, `application/`, `infrastructure/`) live directly under `mixy/`.

### Validation: Pydantic v2
Pydantic v2 for config parsing and domain model validation. It handles YAML-to-model deserialization, type coercion, and error messages. Alternative considered: dataclasses + manual validation — more code, worse error messages.

### Logging: Loguru
Loguru provides structured, colorized CLI-friendly logging out of the box with minimal configuration. Alternative considered: stdlib logging — requires more setup for CLI-quality output.

## Risks / Trade-offs

- [Flat layout may conflict if package is later published] → Can migrate to src layout later if needed; unlikely for a CLI tool
- [Pydantic v2 has breaking changes from v1] → Pin to v2 from the start, no migration needed
