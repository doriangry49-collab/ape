# ADR-0001: Foundation Bootstrap

## Status
Accepted

## Context
APE needs a lightweight, maintainable foundation for future development. The initial scope should be small, dependency-light, and easy to test.

## Decision
Create a minimal Python package with a simple CLI entrypoint and a basic doctor command. Use focused tooling for linting and testing without introducing broader platform dependencies.

## Consequences
- The repository starts with a clear, low-complexity base.
- Future features can build on this structure without major refactoring.
- The documentation can evolve independently while preserving the accepted decision record.
