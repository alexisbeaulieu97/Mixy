# Maintainer Docs

These notes are for contributors and maintainers rather than day-to-day users.

## Internal references

- Product direction: [`product/prd.md`](product/prd.md)
- Implementation roadmap: [`roadmap.md`](roadmap.md)
- Architecture boundary note: application-owned services live in `mixy/application/services` and the source-provider port lives in `mixy/application/ports`; avoid reintroducing imports from the retired compatibility paths.
