# Roadmap

## Sprint 1
- Completed: establish a minimal Python package structure.
- Completed: provide a simple `ape doctor` command for environment inspection.
- Completed: introduce basic test coverage and project metadata.

## Sprint 3
- Completed: add configuration foundation support.
- Completed: implement `ape config` for workspace inspection.
- Completed: add regression tests for configuration behavior.

## Sprint 4 — Workspace Discovery
- Detect an APE workspace from child directories.
- Search parent directories for `.ape/config.toml`.
- Keep existing commands unchanged.
- Add regression tests.
- No new dependencies.

## Near-Term Priorities
- Expand CLI commands only when there is a clear user need.
- Keep dependencies lean and maintainable.
- Document architectural decisions as the project grows.
