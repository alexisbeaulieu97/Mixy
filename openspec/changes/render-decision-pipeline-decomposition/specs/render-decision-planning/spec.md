## ADDED Requirements

### Requirement: Explicit render-decision planning stages
The application SHALL implement render-decision planning through explicit helper stages for source-level preparation and file-level decision assembly behind the shared planning use case.

#### Scenario: Shared planning delegates render-decision stages
- **WHEN** project planning computes render decisions for one or more sources
- **THEN** the work is delegated through smaller render-decision planning stages instead of one monolithic orchestration block

### Requirement: Render-decision behavior preservation
The decomposed render-decision pipeline SHALL preserve current metadata inheritance, effective context resolution, template rendering, and output path planning behavior.

#### Scenario: Recursive metadata still affects rendered output
- **WHEN** a source uses root, directory, and file-scoped metadata
- **THEN** the planned rendered files reflect the same effective defaults, variable resolution, and copy/render policies as before the refactor

#### Scenario: Output-relative paths still respect rendered path settings
- **WHEN** a source file name or parent directories require path rendering decisions
- **THEN** the resulting `RenderedFile.output_relative_path` matches the prior planning behavior
