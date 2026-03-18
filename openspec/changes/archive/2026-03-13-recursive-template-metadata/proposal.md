## Why

Template authors need to declare rendering behavior, variable definitions, and include/exclude rules alongside their template content. Without template-local metadata, all configuration must live in the project config file, which breaks the separation between "what templates contain" and "how templates are composed." Recursive metadata allows templates to be self-describing and portable.

## What Changes

- Implement metadata discovery: `.mixy/template.yml` at directory scope, `<filename>.mixy.yml` at file scope
- Implement scope hierarchy resolution: project defaults → source root → nested directories → file scope
- Implement inheritance rules: scalar fields use nearest-scope-wins, list fields use union, map fields use deep merge with child override
- Implement variable refinement validation — nested scopes may refine (add description, narrow default) but not contradict (change type, incompatible choices) parent variable definitions
- Define allowed and disallowed fields for recursive metadata
- Integrate metadata with template rendering and merge planning decisions

## Capabilities

### New Capabilities
- `template-metadata-discovery`: Recursive discovery of `.mixy/template.yml` directory metadata and `<filename>.mixy.yml` file sidecar metadata within materialized source trees
- `metadata-inheritance`: Scope hierarchy resolution with field-specific inheritance rules for behavioral settings and variable definitions

### Modified Capabilities

## Impact

- Creates `mixy/domain/services/metadata_resolver.py`
- Creates `mixy/domain/models/template_metadata.py`
- Creates `mixy/infrastructure/config/metadata_loader.py`
- Integrates with source resolution (post-materialization) and template rendering (render policy)
- Integrates with variable resolution (template-declared variables merge with project variables)
