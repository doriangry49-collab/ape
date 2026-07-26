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
- **Current Sprint:** Sprint 3 – Configuration Foundation
- **Last Completed Sprint:** Sprint 3 – Configuration Foundation
- **Current Focus:** finalize Sprint 3 documentation and prepare for Sprint 4

## Working Features

- ✅ uv-based project environment
- ✅ Typer CLI
- ✅ `ape doctor`
- ✅ `ape version`
- ✅ `ape init`
- ✅ `ape config`
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

## Next Objective

Sprint 4 – Workspace Discovery

Planned work:

- Detect an APE workspace from child directories.
- Search parent directories for `.ape/config.toml`.
- Keep existing commands unchanged.
- Add regression tests.
- No new dependencies.

## Resume Instructions

When starting a new ChatGPT session:

1. Read this file first.
2. Read `docs/architecture.md`.
3. Read `docs/roadmap.md`.
4. Read `docs/prompts/AGENT_RULES.md`.
5. Continue from the current sprint without redesigning completed components.
## Repository

GitHub is the authoritative source for:

- Code
- Documentation
- Architecture decisions
- Project memory