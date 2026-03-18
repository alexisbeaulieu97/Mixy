## Context

Rendering is where variable values meet template content. The engine must handle three concerns: what to render (policy), how to render (Jinja2), and what not to render (binary detection). Getting binary detection wrong corrupts files; getting undefined handling wrong produces silent failures.

## Goals / Non-Goals

**Goals:**
- Render file contents through Jinja2 with resolved variable context
- Render file and directory names through Jinja2
- Detect and skip binary files automatically
- Strip `.j2` suffix from output filenames
- Fail immediately on undefined Jinja2 variables (StrictUndefined)
- Support exclude patterns for raw copy (e.g., `*.png`, `*.jpg`)

**Non-Goals:**
- Custom Jinja2 filters or extensions (can be added later)
- Template composition/inheritance across sources
- Rendering file permissions or ownership
- Content-aware merge of rendered files (e.g., merging two YAML files)

## Decisions

### Binary detection: null byte heuristic + extension blocklist
Read the first 8192 bytes of a file. If any null bytes are found, treat as binary. Additionally maintain an extension blocklist (`.png`, `.jpg`, `.gif`, `.ico`, `.woff`, `.woff2`, `.ttf`, `.zip`, `.gz`, `.tar`, `.exe`, `.dll`, `.so`, `.dylib`) for fast-path detection without reading the file. Alternative: use the `python-magic` library — adds a system dependency (libmagic) which complicates installation.

### Jinja2 StrictUndefined by default
All templates are rendered with `jinja2.StrictUndefined`. If a variable is referenced in a template but not resolved, rendering fails immediately with the variable name and file path. Alternative: LoggingUndefined — too lenient, produces broken output silently.

### .j2 suffix convention
Files ending in `.j2` are always rendered regardless of other policy settings, and the `.j2` suffix is stripped from the output filename. Example: `Dockerfile.j2` renders to `Dockerfile`. This is a well-understood convention from Ansible and other tools.

### Render policy: render everything text, exclude by pattern
Default behavior: render all text files. Users can specify exclude patterns in template metadata (`render.exclude: ["*.png", "*.min.js"]`) to force raw copy. Files matching exclude patterns are copied without rendering.

## Risks / Trade-offs

- [Null byte heuristic may miss some binary formats] → Extension blocklist covers common cases; edge cases are acceptable for MVP
- [Rendering all text files by default may be slow for large templates] → Acceptable for MVP; can add lazy rendering later
- [StrictUndefined is aggressive] → This is intentional — fail-fast is better than broken output
