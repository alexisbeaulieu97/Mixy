## Why

Mixy must turn abstract source references (a path, a URL) into concrete local directory trees before rendering or merging can happen. A clean source provider abstraction enables multiple source types behind a single interface, and the local directory provider is the simplest starting point that enables end-to-end testing of the pipeline.

## What Changes

- Define a `SourceProvider` protocol with `can_handle`, `resolve`, and `fingerprint` methods
- Create a `MaterializedSource` value object representing a resolved local directory tree with its metadata
- Implement `LocalDirProvider` that validates and wraps a local directory path
- Implement `SourceResolver` domain service that dispatches to the correct provider based on source type
- Create a provider registry for registering and discovering source providers

## Capabilities

### New Capabilities
- `source-provider-contract`: Protocol definition for source providers with resolve, can_handle, and fingerprint methods
- `local-dir-source`: Local directory source provider that validates and materializes filesystem paths

### Modified Capabilities

## Impact

- Creates `mixy/domain/services/source_resolver.py`
- Creates `mixy/infrastructure/sources/base.py` (protocol)
- Creates `mixy/infrastructure/sources/local.py` (local dir provider)
- Creates `mixy/domain/models/materialized_source.py`
