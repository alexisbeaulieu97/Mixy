## 1. Rendering Adapter Extraction

- [x] 1.1 Add a minimal application-owned rendering adapter contract for binary checks, suffix handling, and string rendering
- [x] 1.2 Refactor `TemplateRenderer` to use that adapter while preserving existing behavior and error mapping

## 2. Composition Wiring

- [x] 2.1 Move the default rendering adapter wiring into `mixy/application/composition.py`
- [x] 2.2 Keep Jinja and binary detection as the default infrastructure implementation

## 3. Validation

- [x] 3.1 Add or update focused renderer/composition tests for behavior preservation
- [x] 3.2 Run the focused affected tests
- [x] 3.3 Run the full test suite
