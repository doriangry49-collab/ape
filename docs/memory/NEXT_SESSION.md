# APE – Next Session

## Read Order

Before making any changes, read these files in order:

1. `START_HERE.md`
2. `docs/memory/PROJECT_CONTEXT.md`
3. `docs/architecture.md`
4. `docs/roadmap.md`
5. `docs/prompts/AGENT_RULES.md`

## Current Sprint

Sprint 6 – Project Services

## Current Goal

Evolve the lightweight Project abstraction into reusable internal services for future workspace-aware commands.

Do not redesign the existing CLI.
Keep the architecture simple.
Do not introduce new dependencies without approval.
Continue to preserve the current command behavior and test coverage.

## Development Rules

- Keep the architecture simple.
- One working sprint at a time.
- Every change must be reviewable.
- Every sprint ends with a working system.
- GitHub is the single source of truth.

## Next Planned Work

- Define lightweight project services around configuration and project state.
- Keep commands backward compatible.
- Add or preserve regression coverage.
- No new dependencies.