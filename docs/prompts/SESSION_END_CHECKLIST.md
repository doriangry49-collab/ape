# Session End Checklist

This checklist must be completed before ending any development session.

## Mandatory

- Run `ruff check .`
- Run `pytest -q`
- Run `git status`
- Run `git log --oneline -5`

## Verify

- Working tree is clean.
- Tests are passing.
- Ruff reports no issues.
- The latest implementation commit exists.
- Documentation changes are committed if applicable.
- Nothing is left untracked.

## If changes exist

Never end the session while changes remain.

Either:

- commit them (only after explicit user approval), then push

or

- clearly report every modified and untracked file.

## Final Report

Report only:

- git status
- latest commit
- latest push status
- modified files (if any)
- untracked files (if any)
- test result
- ruff result
