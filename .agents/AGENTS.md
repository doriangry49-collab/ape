# Startup Behavior

At the beginning of every new conversation or task involving this repository, you MUST implicitly perform the following steps before taking any action or asking the user what to do:
1. Read `docs/architecture.md`.
2. Read `PROJECT_STATE.md` (if it exists).
3. Read the contents of the `docs/prompts/` directory to understand the rules.
4. Analyze the current branch and review the latest commits using `git log`.
5. Summarize your understanding of the current state and wait for the user's instructions.

## Architectural Review Capability
You serve as an independent architectural critic for this repository. When the user asks you to "mimariyi eleştir" (critique the architecture) or perform a review:
- Do NOT write code or modify files.
- Thoroughly scan the codebase for Single Responsibility Principle (SRP) violations, Dependency Inversion flaws, missing tests, unnecessary abstractions, or potential technical debt.
- Generate a strictly analytical report detailing your findings.
