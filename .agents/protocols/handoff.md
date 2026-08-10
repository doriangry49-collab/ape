# Protocol: AI Handoff

When concludes a development session, the Operational Agent must produce a clean devir-teslim (handoff) report to ensure continuity.

## Handoff Report Format
The handoff report must be written in the following template:

```text
HANDOFF

REPOSITORY IDENTITY FINGERPRINT
───────────────────────────────
Root        : [Canonical Absolute Path]
Remote      : [Origin Push URL]
Branch      : [Current Branch Name]
HEAD        : [Full Commit SHA]
Timestamp   : [ISO-8601 UTC]

Current Sprint: [Sprint name/number]
Current Objective: [Brief overview of what we are building]

Completed:
  - [x] Item 1
  - [x] Item 2
In Progress:
  - [/] Item 3
Blocked:
  - [ ] Blocked issue (if any)
Architecture Decisions:
  - [Decision detail]
Open Questions:
  - [Question detail]
Files Changed:
  - [List of modified paths]
Tests: [X/Y passed]
Ruff: [0 errors or specific lint warnings]
Git State: [Status, local branch, divergence]
Next Recommended Action: [Action detail]
Do Not Do: [Things to avoid based on Lead Architect instructions]
```

Write the handoff report as your final turn message or save it to `walkthrough.md`. Do not perform any git commits during handoff unless explicitly approved.
