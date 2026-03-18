## 1. Binary Detection

- [x] 1.1 Create `mixy/infrastructure/rendering/binary_detection.py`
- [x] 1.2 Implement extension blocklist for known binary types
- [x] 1.3 Implement null-byte content heuristic (read first 8192 bytes)
- [x] 1.4 Expose `is_binary(path: Path) -> bool` function

## 2. Jinja2 Renderer

- [x] 2.1 Create `mixy/infrastructure/rendering/jinja_renderer.py`
- [x] 2.2 Configure Jinja2 Environment with StrictUndefined
- [x] 2.3 Implement `render_string(template: str, context: dict) -> str` for content and path rendering
- [x] 2.4 Implement `.j2` suffix detection and stripping logic

## 3. Template Renderer Service

- [x] 3.1 Create `mixy/domain/services/template_renderer.py` with `TemplateRenderer` class
- [x] 3.2 Implement `render_file(source_path: Path, context: dict, render_policy) -> RenderedFile` — checks binary, applies exclude patterns, renders content
- [x] 3.3 Implement `render_path(name: str, context: dict) -> str` — renders file/directory names through Jinja2
- [x] 3.4 Implement render policy evaluation — exclude pattern matching using fnmatch
- [x] 3.5 Add `RenderingError` to domain exceptions with file path and variable name

## 4. Tests

- [x] 4.1 Unit tests for binary detection — known extensions, null byte detection, text files
- [x] 4.2 Unit tests for Jinja2 rendering — simple substitution, conditionals, loops, undefined variables
- [x] 4.3 Unit tests for path name rendering
- [x] 4.4 Unit tests for .j2 suffix stripping
- [x] 4.5 Unit tests for exclude pattern matching
- [x] 4.6 Integration test rendering a template directory with mixed binary/text files
- [x] 4.7 Create test fixtures with sample template files in `tests/fixtures/templates/`
