# APE – Next Session

## Read Order

Before making any changes, read these files in order:

1. `START_HERE.md`
2. `docs/memory/PROJECT_CONTEXT.md`
3. `docs/architecture.md`
4. `docs/roadmap.md`
5. `docs/prompts/AGENT_RULES.md`

## Current Sprint

Sprint 4 – Workspace Discovery

## Current Goal

Detect an APE workspace from child directories by searching parent directories for `.ape/config.toml`.

Do not redesign the existing CLI.
Do not introduce new dependencies without approval.
Do not add AI providers or other platform layers.

## Development Rules

- Keep the architecture simple.
- One working sprint at a time.
- Every change must be reviewable.
- Every sprint ends with a working system.
- GitHub is the single source of truth.

## Next Planned Work

- Detect an APE workspace from child directories.
- Search parent directories for `.ape/config.toml`.
- Keep existing commands unchanged.
- Add regression tests.
- No new dependencies.