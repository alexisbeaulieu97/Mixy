## 1. Missing Port Extraction

- [x] 1.1 Add application-owned ports for config loading, vars loading, metadata discovery, source provider registry, and secret masking
- [x] 1.2 Keep the new contract surface minimal and aligned with existing runtime behavior

## 2. Composition Wiring

- [x] 2.1 Move default runtime wiring for the new ports into `mixy/application/composition.py`
- [x] 2.2 Refactor planning/generation use cases and variable-resolution service to consume composition-owned defaults instead of direct infrastructure imports

## 3. Validation

- [x] 3.1 Add or update focused tests for composition and behavior preservation
- [x] 3.2 Run the focused affected tests
- [x] 3.3 Run the full test suite
