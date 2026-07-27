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

## Final Verification (Mandatory)

Before declaring any implementation complete:

1. Run:
   - `ruff check .`
   - `pytest -q`
   - `git status`

2. Verify that:
   - Only the expected files were modified.
   - No unrelated files were changed.
   - No temporary files remain.

3. Never commit unless explicitly instructed.

4. Never push unless explicitly instructed.

5. Report only:
   - modified files
   - git status
   - ruff result
   - pytest result
