# Mixy Docs

This directory contains the user-facing documentation for Mixy.

Use these guides in order if you are new to the project:

1. [`getting-started.md`](getting-started.md)
2. [`configuration.md`](configuration.md)
3. [`variables.md`](variables.md)
4. [`template-authoring.md`](template-authoring.md)
5. [`commands.md`](commands.md)
6. [`merging-and-conflicts.md`](merging-and-conflicts.md)
7. [`git-and-cache.md`](git-and-cache.md)

## Start here

- New to Mixy: [`getting-started.md`](getting-started.md)
- Need a config example: [`configuration.md`](configuration.md)
- Passing values at runtime: [`variables.md`](variables.md)
- Writing reusable templates: [`template-authoring.md`](template-authoring.md)
- Looking for CLI syntax: [`commands.md`](commands.md)
- Debugging collisions between sources: [`merging-and-conflicts.md`](merging-and-conflicts.md)
- Using Git templates and cache commands: [`git-and-cache.md`](git-and-cache.md)

## Internal docs

These files are useful for maintainers, but they are not the primary user docs:

- Product direction: [`product/prd.md`](product/prd.md)
- Implementation roadmap: [`roadmap.md`](roadmap.md)
- Architecture boundary note: application-owned services live in `mixy/application/services` and the source-provider port lives in `mixy/application/ports`; avoid reintroducing imports from the retired compatibility paths.
