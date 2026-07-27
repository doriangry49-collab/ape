# APE – Project Context

> This file is the single source of truth for resuming the project in a new ChatGPT session.

## Project Identity

- **Name:** APE (Autonomous Production Engine)
- **Repository:** https://github.com/doriangry49-collab/ape
- **Primary Environment:** GitHub Codespaces
- **Language:** Python 3.12
- **Package Manager:** uv
- **Source of Truth:** GitHub

## Current Status

- **Version:** v0.1.0
- **Current Sprint:** Sprint 6.2 – Project Services
- **Last Completed Sprint:** Sprint 6.1 – Project Services
- **Current Focus:** build reusable project information services and prepare the future service layer while preserving CLI behavior and test coverage

## Working Features

- ✅ uv-based project environment
- ✅ Typer CLI
- ✅ `ape doctor`
- ✅ `ape version`
- ✅ `ape init`
- ✅ `ape config`
- ✅ Workspace discovery
- ✅ Shared workspace module at `src/ape/workspace.py`
- ✅ Project configuration support
- ✅ Built-in TOML parsing via `tomllib`
- ✅ `Project.config` property
- ✅ `Project.name` property
- ✅ `Project.metadata` property
- ✅ Read-only Project API
- ✅ pytest
- ✅ Ruff
- ✅ Basic project structure

## Architecture Principles

1. Simplicity before complexity.
2. One working sprint at a time.
3. GitHub is the single source of truth.
4. Every feature must be testable.
5. Avoid unnecessary dependencies.
6. Documentation is part of the product.

## Technology Stack

- Python 3.12
- uv
- Typer
- Rich
- pytest
- Ruff
- GitHub Codespaces

## Quality Gate

A sprint is considered complete only if all of the following pass:

- `uv sync`
- `uv run ape doctor`
- `pytest`
- `ruff check .`
- `git status` is clean
- GitHub remains the source of truth for repository state
- Current verification status: 16 passing tests

## Next Objective

Sprint 6.2 – Project Services

Planned work:

- Expand reusable project information services for the future service layer.
- Keep commands backward compatible.
- Preserve test coverage and CLI behavior.
- No new dependencies.

## Resume Instructions

When starting a new ChatGPT session:

1. Read [PROJECT_SNAPSHOT.md](../../PROJECT_SNAPSHOT.md) first.
2. Read this file next.
3. Read `docs/architecture.md`.
4. Read `docs/roadmap.md`.
5. Read `docs/prompts/AGENT_RULES.md`.
6. Continue from the current sprint without redesigning completed components.

## Repository

GitHub is the authoritative source for:

- Code
- Documentation
- Architecture decisions
- Project memory