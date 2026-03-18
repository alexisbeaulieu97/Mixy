## ADDED Requirements

### Requirement: Validation runs through the application layer
The system SHALL provide an application-owned validation use case for command consumers.

#### Scenario: CLI validate uses the application seam
- **WHEN** the user runs `mixy validate CONFIG_PATH`
- **THEN** the CLI obtains validation results through an application use case instead of orchestrating loading and validation directly
