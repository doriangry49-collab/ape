# Release Checklist

## Pre-release
- Review the current sprint status and project context.
- Confirm the documented features match the implementation.
- Verify the CLI commands remain backward compatible.
- Run `ruff check .`.
- Run `pytest -q`.
- Review the changelog and project state documents.

## Release Notes
- Confirm the current version is `v0.1.0`.
- Note the completed Sprint 4 workspace discovery work.
- Note the extracted workspace module at `src/ape/workspace.py`.
- Record the tested CLI commands: `doctor`, `version`, `init`, and `config`.

## Final Check
- Ensure documentation is current.
- Ensure no code or tests were changed as part of documentation-only work.
- Do not commit or push.
