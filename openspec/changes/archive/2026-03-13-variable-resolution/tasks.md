## 1. Variable Resolver Service

- [x] 1.1 Create `mixy/domain/services/variable_resolver.py` with `VariableResolver` class
- [x] 1.2 Implement precedence chain: defaults → env → vars file → per-source → CLI
- [x] 1.3 Implement `resolve_all(definitions, global_values, source_values, cli_overrides, env_prefix) -> dict[str, Any]`
- [x] 1.4 Implement per-source context builder that merges global resolved values with source-specific overrides

## 2. Type Coercion and Validation

- [x] 2.1 Implement type coercion from strings to declared types (str, int, float, bool) using Pydantic
- [x] 2.2 Implement choices constraint validation
- [x] 2.3 Implement pattern (regex) constraint validation
- [x] 2.4 Add `VariableResolutionError` to domain exceptions with variable name, value, and reason

## 3. Value Sources

- [x] 3.1 Implement environment variable reader with `MIXY_VAR_` prefix convention
- [x] 3.2 Create `mixy/infrastructure/config/vars_file_loader.py` for loading YAML vars files
- [x] 3.3 Implement CLI `--var KEY=VALUE` parsing into dict

## 4. Interactive Prompting

- [x] 4.1 Implement interactive prompt for unresolved required variables using typer.prompt
- [x] 4.2 Show variable description and choices in prompt
- [x] 4.3 Implement `--non-interactive` mode that raises error instead of prompting
- [x] 4.4 Handle secret variables with password-style input (hidden echo)

## 5. Secret Masking

- [x] 5.1 Implement loguru filter that replaces secret values with `***`
- [x] 5.2 Register filter after variable resolution completes

## 6. Tests

- [x] 6.1 Unit tests for precedence chain — each layer overrides correctly
- [x] 6.2 Unit tests for type coercion — valid casts, invalid casts, edge cases (bool parsing)
- [x] 6.3 Unit tests for constraint validation — choices, pattern, combinations
- [x] 6.4 Unit tests for env var reading with prefix
- [x] 6.5 Unit tests for vars file loading
- [x] 6.6 Unit tests for per-source context merging
- [x] 6.7 Integration test for interactive prompting (mock stdin)
- [x] 6.8 Unit test for secret masking in log output
