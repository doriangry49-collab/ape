# Architecture Decisions

## ADR-0001 GitHub is the source of truth
- The repository on GitHub is the authoritative source for code, documentation, and project state.
- Local workspace changes must remain aligned with the remote repository.

## ADR-0002 Documentation first
- Documentation is treated as part of the product foundation.
- Project memory, architecture, and implementation guidance must stay aligned with the codebase.

## ADR-0003 Workspace discovery
- APE resolves workspace boundaries by locating an APE workspace from the current directory or parent directories.
- Workspace discovery is shared through the lightweight workspace helper.

## ADR-0004 Read-only Project abstraction
- The Project abstraction is intentionally lightweight and read-only for configuration and metadata access.
- It serves as the shared internal entry point for future workspace-aware commands.

## ADR-0005 No unnecessary dependencies
- The project keeps its dependency footprint minimal.
- New dependencies are avoided unless explicitly required.

## ADR-0006 Backward compatible CLI
- Existing CLI commands and output should remain stable.
- New abstractions must not change the public CLI surface.

## ADR-0007 Test-first verification
- New behavior must be covered by regression tests.
- Validation is expected through Ruff and pytest before completion is declared.
