# Architecture

## Overview
APE is a minimal Python CLI foundation for future product development. Sprint 1 is complete, and Sprint 1.1 is focused on documenting the project memory and architecture.

## Current Structure
- `src/ape/cli.py` exposes the command-line entrypoint.
- `src/ape/doctor.py` collects a lightweight environment snapshot.
- `src/ape/__init__.py` defines package metadata.
- Tests live under `tests/` and cover the current CLI behavior.
- Documentation lives under `docs/` and is treated as part of the project foundation.

## Design Principles
- Keep the dependency footprint minimal.
- Favor clear, readable Python over framework-heavy abstractions.
- Preserve a simple path for future feature expansion.
- Keep documentation aligned with the current implementation.
