# Protocol: Commit Gate

Before code can be committed or pushed, the Operational Agent MUST satisfy the Commit Gate checklist.

## 1. Explicit Commit Approval
You must NEVER commit or push changes unless the Lead Architect explicitly writes:
`COMMIT APPROVED`
Any other phrasing ("looks good", "continue", "okay", "pass") is NOT an approval.

## 2. Pre-Commit Checklist
Before requesting commit approval, run the Repository Health Check:
```bash
git fetch origin
git status
git log --oneline HEAD..origin/main
ruff check .
pytest -q
```

## 3. Commit Discipline Rules
- **Single Responsibility:** Each commit must have exactly one purpose. Do not bundle unrelated changes (e.g. refactoring utils and adding a command) in a single commit.
- **Clean Git Status:** Ensure all ephemeral files (.build/, .venv/, etc.) are correctly ignored and do not appear in `git status`.
- **Zero Linters:** Python code must have 0 ruff errors.
- **100% Green Tests:** All tests must pass.
