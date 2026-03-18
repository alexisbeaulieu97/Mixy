## Why

Mixy templates contain Jinja2 expressions in both file contents and file/directory names. The rendering engine must decide which files to render, detect binary files to avoid corruption, and enforce strict undefined variable handling so errors are caught early rather than producing broken output.

## What Changes

- Implement `TemplateRenderer` domain service that renders Jinja2 templates with resolved variables
- Implement binary file detection to prevent rendering binary files
- Implement file and directory path name rendering (e.g., `{{ project_name }}/main.py`)
- Support render policy: render all text files by default, opt-out via exclude patterns
- Use Jinja2 StrictUndefined to fail on unresolved variables
- Support `.j2` suffix stripping: files ending in `.j2` are always rendered and the suffix is removed from output

## Capabilities

### New Capabilities
- `template-rendering`: Jinja2 template rendering for file contents and path names with binary detection, strict undefined, and render policy
- `binary-detection`: Heuristic binary file detection to prevent rendering non-text files

### Modified Capabilities

## Impact

- Creates `mixy/infrastructure/rendering/jinja_renderer.py`
- Creates `mixy/infrastructure/rendering/binary_detection.py`
- Creates `mixy/domain/services/template_renderer.py`
- Integrates with variable resolution for the template context
