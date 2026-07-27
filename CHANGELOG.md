# Changelog

## v0.1.0

### Sprint 1
- Foundation
- uv
- Typer
- `ape doctor`

### Sprint 1.1
- Documentation
- Architecture
- Project memory
- ADR
- Roadmap

### Sprint 2
- `ape version`
- `ape init`

### Sprint 3
- `ape config`
- Configuration support

### Sprint 4
- Workspace discovery
- Parent directory lookup
- Shared workspace module
- CLI refactoring for workspace lookup
- Regression tests
- Verified `ape doctor`, `ape version`, `ape init`, and `ape config`

### Sprint 5
- Project configuration support
- Built-in TOML parsing via `tomllib`
- Added `Project.config` property
- Added read-only Project properties
- Added regression tests for config loading and missing-config fallback
- Verified 13 passing tests
- No new dependencies
