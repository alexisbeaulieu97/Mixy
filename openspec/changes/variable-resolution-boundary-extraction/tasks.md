## 1. Domain Purification

- [x] 1.1 Remove Typer prompting ownership from `mixy/domain/services/variable_resolver.py`
- [x] 1.2 Remove Loguru secret-masking side effects from the domain resolver
- [x] 1.3 Keep precedence, coercion, validation, and CLI override parsing behavior stable

## 2. Application / Infrastructure Seams

- [x] 2.1 Add an application-owned variable-resolution service that coordinates optional prompting and prompt-cache reuse
- [x] 2.2 Add a `PromptGateway` port and a concrete runtime prompt adapter
- [x] 2.3 Add an infrastructure logging helper for secret masking and wire it through the application-owned service

## 3. Use-Case Integration and Validation

- [x] 3.1 Update planning/generation flows to use the application-owned variable-resolution seam
- [x] 3.2 Update or add focused tests for prompting, non-interactive failures, and secret masking after the move
- [x] 3.3 Run the focused variable-resolution tests and the full test suite, then mark tasks complete
