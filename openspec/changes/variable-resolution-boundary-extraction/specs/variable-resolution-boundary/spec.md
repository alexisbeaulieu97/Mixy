## ADDED Requirements

### Requirement: Domain-owned variable resolution stays pure
The domain variable resolver SHALL resolve precedence, coercion, and validation rules without directly prompting users or mutating logging configuration.

#### Scenario: Missing required variable in the domain
- **WHEN** the domain resolver encounters a required variable with no available value
- **THEN** it reports the unresolved variable as an error instead of prompting directly

### Requirement: Application-owned interactive prompting
The application layer SHALL own optional prompting for missing required variables through a prompt gateway.

#### Scenario: Interactive planning prompts once and reuses the answer
- **WHEN** planning runs in interactive mode and a required variable is missing
- **THEN** the application-owned variable-resolution service prompts through the prompt gateway, retries resolution, and reuses the prompted value for later planning steps

#### Scenario: Non-interactive planning still fails fast
- **WHEN** planning runs in non-interactive mode and a required variable is missing
- **THEN** the application-owned variable-resolution service surfaces the unresolved-variable error without prompting

### Requirement: Secret masking remains available outside the domain
Secret values resolved during planning SHALL continue to be masked in runtime log output without the domain resolver configuring logging directly.

#### Scenario: Resolved secret is masked in logs
- **WHEN** a secret variable value is resolved during planning
- **THEN** subsequent runtime log output masks that secret value
