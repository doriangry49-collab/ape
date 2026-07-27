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

## Architectural Review Capability
Before concluding significant sprints or proposing/implementing new services, you MUST perform an architectural review.
- Do NOT write code or modify files during the review.
- Look for: SRP violations, Dependency Inversion violations, Hollow abstraction / Anemic service, Unnecessary abstraction, Technical debt, Test organization, Cross-platform problems, YAGNI, KISS.
- You must not assume current suggestions are automatically correct. Challenge them.
- For each finding, report in this exact format:
  * Evidence (file/lines)
  * Neden problem olduğu (Why it's a problem)
  * Alternatif çözüm (Alternative solution)
  * Trade-off
  * Risk
  * Fix Now / Postpone / Reject
- After generating the report, produce an implementation plan for the "Fix Now" items.

## Explicit Commit Approval Rule
I must never create a commit or push changes unless the user explicitly writes:
`COMMIT APPROVED`
Any other wording ("looks good", "continue", "okay", "evaluate", etc.) must not be interpreted as commit approval.
