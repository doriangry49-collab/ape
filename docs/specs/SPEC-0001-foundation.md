# SPEC-0001: Foundation

## Goal

Define the project foundation for APE, including the supported runtime and core tooling.

## Requirements

- Target Python version: 3.12.
- Use `uv` for environment and dependency management.
- Provide a Typer-based CLI entry point.
- Use Rich for interactive output where appropriate.
- Use Ruff for linting.
- Use pytest for automated tests.
- Support GitHub Codespaces as the primary development environment.

## Non-Goals

- Full application runtime beyond the initial CLI foundation.
- New runtime dependencies outside the existing toolchain.

## Implementation Notes

The foundation should remain minimal and predictable. The package layout, CLI entry points, and development tooling should be easy to understand and maintain.

## Tests

- Validate project import and CLI entry points.
- Ensure the basic development workflow remains functional.

## Acceptance Criteria

- The project can be installed and run in a Python 3.12 environment.
- The documented tooling stack is available and usable.
- The foundation remains simple and consistent with the current repository structure.
