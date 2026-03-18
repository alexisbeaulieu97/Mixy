## Why

The CLI is the user's interface to Mixy. A well-designed CLI with clear commands, consistent options, helpful error messages, and progress reporting determines whether Mixy feels reliable or frustrating. The `version` command exists from bootstrap, but the core commands (`generate`, `validate`, `inspect`) need to be wired to the application layer.

## What Changes

- Implement `mixy generate CONFIG_PATH` command with all options: `--output`, `--var`, `--vars-file`, `--non-interactive`, `--dry-run`, `--overwrite`
- Implement `mixy validate CONFIG_PATH` command that checks config validity without generating
- Implement `mixy inspect CONFIG_PATH` command that shows resolved variables, source order, and expected outputs
- Configure loguru for CLI-quality output: colored levels to stderr, structured debug logs
- Format domain errors into user-friendly CLI messages with suggestions
- Add progress reporting for source fetching and file generation
- Support `--quiet` mode that suppresses non-error output

## Capabilities

### New Capabilities
- `cli-generate-command`: The main `mixy generate` CLI command with all options wired to the generation pipeline
- `cli-validate-command`: Config validation command that reports issues without generating files
- `cli-inspect-command`: Config inspection command showing resolved state — variables, sources, merge plan
- `cli-error-formatting`: User-friendly error display with context, suggestions, and appropriate exit codes

### Modified Capabilities

## Impact

- Creates `mixy/cli/commands/generate.py`
- Creates `mixy/cli/commands/validate.py`
- Creates `mixy/cli/commands/inspect.py`
- Modifies `mixy/cli/app.py` to register all commands
- Creates `mixy/infrastructure/logging/logger.py` for loguru configuration
