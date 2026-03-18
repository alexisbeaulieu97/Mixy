## Why

Templates contain variables like `{{ project_name }}` that must be resolved to concrete values before rendering. The resolution strategy must be predictable, support multiple value sources with clear precedence, and prompt interactively only as a last resort for unresolved required values.

## What Changes

- Implement `VariableResolver` domain service with a layered precedence chain
- Support value sources: defaults, environment variables, vars files (YAML), per-source overrides, CLI `--var` overrides
- Prompt interactively for unresolved required variables when in interactive mode
- Type coercion: cast resolved values to declared variable types (str, int, float, bool)
- Validate resolved values against constraints (choices, pattern)
- Mask secret variable values in all log output

## Capabilities

### New Capabilities
- `variable-resolution`: Layered variable resolution with precedence chain, type coercion, constraint validation, and interactive prompting

### Modified Capabilities

## Impact

- Creates `mixy/domain/services/variable_resolver.py`
- Creates `mixy/infrastructure/config/vars_file_loader.py`
- Integrates with CLI layer for `--var` and `--vars-file` options
- Affects logging infrastructure for secret masking
