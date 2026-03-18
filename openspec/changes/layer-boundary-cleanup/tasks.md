## 1. Application Ownership Migration

- [x] 1.1 Add application-layer modules for `SourceProvider`, `SourceResolver`, and `TemplateRenderer`
- [x] 1.2 Update planning, generation, plugin, and provider-related imports to use the new application ownership boundaries
- [x] 1.3 Reduce `mixy/domain/services/` to pure policy services only, allowing only thin migration shims if they are necessary for safety

## 2. Validation

- [x] 2.1 Update or add focused tests covering source resolution, template rendering, and planning imports after the move
- [x] 2.2 Run the relevant focused tests and the full test suite
- [x] 2.3 Update this task list to reflect completion
