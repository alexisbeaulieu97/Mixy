## Why

The individual components — config loading, variable resolution, source resolution, rendering, and merge planning — must be orchestrated into a single coherent pipeline. The generation pipeline is the primary use case of Mixy: take a config file and produce a project directory. Without this orchestration layer, the components have no consumer.

## What Changes

- Implement `generate_project` application use case that orchestrates the full pipeline
- Implement `GenerationExecutor` infrastructure service that writes RenderPlan operations to the filesystem
- Support `--dry-run` mode that builds and displays the plan without writing
- Support `--output` path override
- Emit a structured summary after generation (files created, rendered, copied raw, skipped)
- Handle partial failure — if a write fails, report which operations succeeded and which failed

## Capabilities

### New Capabilities
- `generation-pipeline`: End-to-end project generation orchestrating config loading, validation, source resolution, variable resolution, merge planning, and file writing
- `dry-run-mode`: Preview generation plan without writing files, showing all planned operations

### Modified Capabilities

## Impact

- Creates `mixy/application/use_cases/generate_project.py`
- Creates `mixy/infrastructure/filesystem/file_writer.py`
- Integrates all previously built domain services into one flow
- Integrates with CLI layer for the `mixy generate` command
