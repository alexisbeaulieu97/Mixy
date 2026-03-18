## 1. Logging Configuration

- [x] 1.1 Create `mixy/infrastructure/logging/logger.py` with loguru setup function
- [x] 1.2 Configure stderr handler with colored format: `{level.icon} {message}`
- [x] 1.3 Configure debug format: `{time} {level} {name}:{line} {message}`
- [x] 1.4 Implement `--quiet` mode (WARNING level)
- [x] 1.5 Wire log level configuration to `--log-level` global option

## 2. Generate Command

- [x] 2.1 Create `mixy/cli/commands/generate.py` with Typer command
- [x] 2.2 Add options: `--output`, `--var` (repeatable), `--vars-file`, `--non-interactive`, `--dry-run`, `--overwrite`
- [x] 2.3 Wire to `generate_project` use case with constructed dependencies
- [x] 2.4 Handle and format errors from each pipeline stage

## 3. Validate Command

- [x] 3.1 Create `mixy/cli/commands/validate.py` with Typer command
- [x] 3.2 Wire to config loading and validation
- [x] 3.3 Display all validation issues (not just first)
- [x] 3.4 Print success message on valid config

## 4. Inspect Command

- [x] 4.1 Create `mixy/cli/commands/inspect.py` with Typer command
- [x] 4.2 Display resolved variables table
- [x] 4.3 Display source list with type and path/URL
- [x] 4.4 Display merge preview with output paths per source

## 5. Error Formatting

- [x] 5.1 Create error formatting utility for domain exceptions
- [x] 5.2 Map exception types to exit codes (0=success, 1=user error, 2=system error)
- [x] 5.3 Format errors with type, message, field path, and suggestion
- [x] 5.4 Handle unexpected exceptions with generic message + debug hint

## 6. Command Registration

- [x] 6.1 Register generate, validate, inspect commands in `mixy/cli/app.py`
- [x] 6.2 Verify all commands appear in `mixy --help`

## 7. Tests

- [x] 7.1 CLI test: `mixy generate --help` shows all options
- [x] 7.2 CLI test: `mixy validate` with valid config exits 0
- [x] 7.3 CLI test: `mixy validate` with invalid config exits 1
- [x] 7.4 CLI test: `mixy inspect` outputs variable and source tables
- [x] 7.5 CLI test: error formatting produces readable output
- [x] 7.6 CLI test: `--quiet` suppresses info-level output
- [x] 7.7 CLI test: exit codes match expected values
