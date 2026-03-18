## Context

The CLI commands are thin wrappers that parse arguments, construct dependencies, call application use cases, and format output. They should contain minimal logic — just enough to translate between the terminal and the application layer.

## Goals / Non-Goals

**Goals:**
- Clean Typer command definitions with well-documented options
- Consistent error handling: catch domain exceptions and format them for humans
- Appropriate exit codes: 0 for success, 1 for user errors, 2 for system errors
- Loguru configured per command: stderr for logs, stdout for data output
- Progress reporting with loguru status messages (not progress bars)
- `--quiet` suppresses info-level output

**Non-Goals:**
- Interactive TUI or dashboard
- JSON output mode (can be added later)
- Shell completion generation
- Config file generation/scaffolding wizard

## Decisions

### Commands as separate modules under cli/commands/
Each command gets its own module for readability. The main `app.py` imports and registers them. This keeps the CLI layer organized as commands grow.

### Error formatting: catch and translate
Each command wraps its use-case call in a try/except that catches domain exceptions (ConfigValidationError, SourceResolutionError, etc.) and formats them with rich-style output: error type, message, suggestion, and the relevant file/field path. Unhandled exceptions get a generic "unexpected error" message with a debug log hint.

### Loguru configuration
- Logs go to stderr (so stdout is clean for data like inspect output)
- Default level: INFO
- `--log-level debug` enables DEBUG
- `--quiet` sets level to WARNING
- Format: `{level.icon} {message}` for user-facing, `{time} {level} {name}:{line} {message}` for debug

### Inspect command output format
`mixy inspect` outputs a structured summary:
- Config: name, version, source count
- Variables: name, type, resolved value (or "unresolved"), source of value
- Sources: id, type, path/URL, status
- Merge preview: output paths grouped by source

## Risks / Trade-offs

- [Loguru custom format may conflict with CI log parsers] → Users can set `--log-level` appropriately; structured JSON output is a future option
- [Inspect command requires resolving sources to show full plan] → Accept this; warn if source resolution fails and show partial results
