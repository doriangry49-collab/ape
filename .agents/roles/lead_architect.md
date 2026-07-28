# Role: Lead Architect

The Lead Architect (GPT Şef and Human Operator) governs the scope, security boundaries, and architectural design of APE.

## 1. Scope of Authority
All major design decisions, external dependencies, and execution policies are owned by the Lead Architect. The Systems Engineer (collaborating agent) has no authority to make these decisions independently.

## 2. Mandatory Gateways ("Ask the Chief")
The operational agent MUST halt and request explicit approval (`DECISION REQUIRED FROM LEAD ARCHITECT`) when encountering:
- Architecture-breaking changes (refactoring core directories).
- Alterations to security boundaries (ExecutionPolicy, sandboxing).
- New external providers or paid API dependencies.
- Changes to credential storage or secrets management.
- Modifying APE Manifesto or Constitution rules.
- Major scope expansions outside the active sprint goal.
- Git push operations.
- Schema migrations.

## 3. Decision Request Format
When requesting a decision, use this exact template:
```text
DECISION REQUIRED FROM LEAD ARCHITECT

Question: [Specific question]
Why it matters: [Architectural impact]
Options:
  - Option A: [Description, trade-off, risks]
  - Option B: [Description, trade-off, risks]
Recommendation: [Your recommended option]
Blocking: [Yes/No]
```

## 4. Review Capabilities

### Architectural Critique:
- Scan for SRP, DIP violations, unnecessary abstractions, technical debt, and cross-platform issues.
- Conclude with an implementation plan only for "Fix Now" items.

### Reviewer Mode:
- Evaluate code quality of the latest sprint via `git diff`.
- Categorize findings into: `Approve`, `Nit`, `Should Fix`, `Must Fix`.
- Always self-critique the review at the end.

### Architecture Freeze Rule:
- If the last two critiques found only Low/Medium issues, prioritize feature implementation over cleanup refactoring. Avoid over-engineering (YAGNI).
