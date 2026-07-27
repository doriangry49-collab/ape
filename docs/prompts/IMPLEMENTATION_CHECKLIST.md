# Implementation Checklist

## Before Implementation
- Read START_HERE.md
- Read AGENT_RULES.md
- Read the relevant SPEC document (if any)
- Read the existing implementation before making changes

## During Implementation
- Keep changes minimal
- Do not redesign working components
- Do not introduce new dependencies
- Preserve existing CLI behavior unless explicitly requested
- Add or update tests for new behavior

## Before Completion
- Run `ruff check .`
- Run `pytest -q`
- Run `git status`
- Summarize modified files
- Do not commit
- Do not push
