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

## Repository Health (Mandatory)

Before ending any implementation session, always verify:

- `git status`
- `git log --oneline -5`
- `git branch -vv`
- `ruff check .`
- `pytest -q`

If implementation was completed:

- Confirm the commit exists.
- Confirm push succeeded.
- Confirm the working tree is clean.
- Confirm the current branch is synchronized with origin.

If any verification fails, stop and report the problem before ending the session.

## Repository Health Verification

Before declaring a session complete, verify ALL of the following:

- `git status`
- latest commit
- latest push
- current branch
- branch tracking status
- Ruff passes
- Pytest passes
- no unintended files remain
- no `__pycache__` directories are staged
- no temporary files are staged

Never assume work is finished because a commit was created.
A session is complete only after the repository is verified to be clean and synchronized with origin.
