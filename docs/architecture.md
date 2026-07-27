# APE Architecture

## Project Purpose
APE is a minimal Python CLI foundation designed to be a starting point for future product development. Its core design philosophy emphasizes low dependencies, strict documentation discipline, and clear, readable Python code.

## High Level Architecture
The architecture follows a clean separation of concerns:
- **Presentation**: Handled entirely by the CLI layer (`typer`).
- **Orchestration & Business Logic**: Encapsulated within the Services Layer.
- **Data & State**: Represented by a lightweight `Project` model and `Workspace` discovery mechanisms.

## Repository Structure
- `src/ape/`: Core application logic, CLI definitions, and service layers.
- `docs/`: Comprehensive project documentation, ADRs, roadmaps, and strict agent guidelines.
- `tests/`: Automated test suites (`pytest`).

## Layer Responsibilities

### CLI Layer
Located in `src/ape/cli.py`. Strictly acts as an orchestration layer. It parses arguments, invokes the necessary services, and handles terminal output (`typer.echo`). It contains no raw business logic.

### Services Layer
Located in `src/ape/services/`. This layer houses all the core logic and operations. Services are designed to be lightweight, read-only (where possible), and independent. They act on the `Project` model.

### Project Layer
Located in `src/ape/project.py`. Provides a lightweight abstraction (`Project`) over the `.ape/config.toml` configuration. It handles basic TOML parsing and exposes read-only properties to the services.

### Workspace Layer
Located in `src/ape/workspace.py`. Responsible purely for directory discovery (searching upward for the `.ape/config.toml` structure).

### Doctor Layer
Located in `src/ape/doctor.py`. Provides basic, environment-level diagnostic capabilities (Python version, OS platform) formatted for `rich` table output.

## Current Services

### ConfigService
- **Purpose**: Access project configuration.
- **Responsibility**: Exposes configuration paths and parsed TOML data safely.
- **Used Classes**: `Project`
- **Dependencies**: None.

### ProjectInfoService
- **Purpose**: General project information and workspace initialization.
- **Responsibility**: Creating new `.ape` directories, writing default `config.toml`, and proxying basic project info.
- **Used Classes**: `Project`, `ConfigService`, `WorkspaceService`
- **Dependencies**: Requires existing `Project` object.

### ProjectValidationService
- **Purpose**: Validate the state and integrity of the current workspace.
- **Responsibility**: Checks if a workspace exists and if a configuration is present. Yields validation errors.
- **Used Classes**: `Project`, `ConfigService`, `WorkspaceService`
- **Dependencies**: Requires existing `Project` object.

### WorkspaceService
- **Purpose**: Manage and discover workspace paths.
- **Responsibility**: Uses `find_workspace_dir` to determine execution paths and resolves target directories.
- **Used Classes**: `find_workspace_dir`
- **Dependencies**: Relies on standard library `pathlib`.

### DoctorService
- **Purpose**: Compose validation and configuration state for diagnostics.
- **Responsibility**: Runs validations, compiles errors/warnings, and reports the overall project health status (e.g., "invalid" vs "ok").
- **Used Classes**: `Project`, `ConfigService`, `ProjectValidationService`, `WorkspaceService`
- **Dependencies**: Requires existing `Project` object.

## Command Flow

### init
1. Resolves the current working directory.
2. Loads the `Project` abstraction.
3. Instantiates `ProjectInfoService`.
4. Invokes `initialize_workspace` to discover/create `.ape/config.toml`.
5. Prints the creation status to the terminal.

### config
1. Loads the `Project`.
2. Instantiates `ProjectInfoService`, `ProjectValidationService`, and `ConfigService`.
3. Validates the workspace via `ProjectValidationService`. If invalid, exits with code 1.
4. Outputs the root path and config path via `typer.echo`.

### doctor
1. Loads the `Project`.
2. Instantiates `DoctorService` and invokes `run()`.
3. Invokes `run_doctor` from the Doctor Layer, which prints system/platform stats using `rich`.

## Dependency Rules
- **CLI** -> Imports `Services`, `Project`, and `Doctor`.
- **Services** -> Import `Project` and other sibling `Services`.
- **Project** -> Imports `Workspace` (for discovery utilities).
- **Workspace/Doctor** -> Import only standard libraries and external formatting (`rich`).
*(Lower layers never import higher layers. Business logic does not depend on the CLI layer).*

## Testing Strategy
- **pytest**: The primary test runner. Currently heavily focused on integration testing the CLI behavior in a single module.
- **ruff**: Used strictly for linting and code formatting validation (enforcing PEP8, sorting imports).
- **Repository Health Verification**: A strict workflow requirement demanding `pytest -q`, `ruff check .`, and a clean `git status` before any commit is considered valid.

## Repository Workflow
The project adheres to a highly disciplined commit strategy:
- **Küçük Commit**: Changes are atomic and focus on one logical unit.
- **Önce Test**: TDD principles apply; tests are established before implementations.
- **Sonra Implementasyon**: Code is written strictly to pass the defined tests.
- **Commit Öncesi Verification**: No commits are made without running the full health suite (pytest, ruff, git status).

## Current Project Status
Sprint 6.1 (Project Services) is complete. The logic has been successfully extracted from the CLI and `Project` class into a dedicated, modular Services layer. The `Project` model is now primarily read-only.

## Technical Debt
- **Monolithic Test File**: `tests/test_doctor.py` is large (approx 13KB) and contains tests for multiple components. Needs splitting into service-specific tests.
- **Environment Variable Reliance**: Use of `os.environ.get("PWD")` in `cli.py` and `workspace_service.py` may cause cross-platform inconsistencies (e.g., on Windows).

## Sprint History
- **Sprint 4**: Workspace Discovery (detecting `.ape` directories).
- **Sprint 5**: Project Model (introducing lightweight `Project` abstraction and TOML parsing).
- **Sprint 6.1**: Project Services (refactoring logic into modular service classes, shrinking CLI responsibility).

## Roadmap
- **Sprint 2**: Extend diagnostic features and basic test coverage.
- **Sprint 3**: Add foundational configuration management and inspection.
- **Sprint 4**: Solidify upward workspace discovery.
*(Note: As per documented roadmap, the project is currently in the Sprint 6+ phase. Future near-term priorities focus on expanding reusable services and maintaining backward compatibility.)*
