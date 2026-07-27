# Agent Rules

- Never redesign working components.
- Never introduce dependencies without approval.
- Preserve document structure.
- Make one logical change per commit.
- Review before commit.
- Update PROJECT_CONTEXT.md after every sprint.
- Update NEXT_SESSION.md after every sprint.
- Append only to SESSION_LOG.md.
- ADR files record architectural decisions and should not be rewritten after acceptance.
- Do not introduce AI libraries, Docker, MCP, LiteLLM, databases, or networking unless explicitly requested.
- Keep documentation aligned with the current repository state.
- Prefer minimal, maintainable changes.
# Agent Rules

## General

- Never redesign working components.
- Never introduce dependencies without approval.
- Preserve document structure.
- Prefer updating existing files over rewriting them.
- Make one logical change per commit.
- Review before commit.
- Keep documentation aligned with the current repository state.
- Prefer minimal, maintainable changes.

## Sprint Workflow

- Begin every implementation by reading [PROJECT_SNAPSHOT.md](../../PROJECT_SNAPSHOT.md).
- Complete one sprint before starting another.
- Every sprint must end with a working system.
- Update PROJECT_CONTEXT.md after every sprint.
- Update NEXT_SESSION.md after every sprint.
- Append only to SESSION_LOG.md.
- Update ROADMAP.md when sprint status changes.

## Architecture

- GitHub is the single source of truth.
- Simplicity before complexity.
- Avoid unnecessary abstractions.
- Do not introduce AI libraries, Docker, MCP, LiteLLM, databases, networking, or external services unless explicitly requested.

## Repository Safety

Never assume work is finished.

Before considering a task complete, always verify:

- `git status`
- latest commit
- latest push
- Ruff
- Pytest

If the repository is not clean, explicitly report why.
Never silently leave uncommitted work.

## Review

Before proposing a commit, verify:

- `ruff check .`
- `pytest -q`
- `git status`
- Relevant documentation updated

## ADR

- ADR files record architectural decisions.
- Accepted ADR files are append-only.
