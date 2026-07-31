# APE AI Collaboration Layer (RFC-008)

This directory defines the roles, protocols, and skills for AI agents collaborating on the APE project. All agents must read and follow these definitions to ensure consistent development.

## 1. Directory Structure

- **Roles:** Define permissions, authority scopes, and boundaries for human and agent roles.
- **Protocols:** Define step-by-step processes for lifecycle events (startup, concluding sessions, committing code).
- **Skills:** Operational domain-specific rules (TDD, safety, artifact lifecycles) for day-to-day coding.

---

## 2. Directory Index

### Roles (Read at startup or when role assignment shifts)
- **[Lead Architect](file:///.agents/roles/lead_architect.md):** Defines GPT Şef / Human Operator boundaries and decision escalation requirements ("Ask the Chief").
- **[Systems Engineer](file:///.agents/roles/systems_engineer.md):** Defines Antigravity's operational limits and guidelines.

### Protocols (Read and trigger on event boundaries)
- **[Session Bootstrap](file:///.agents/protocols/session_bootstrap.md):** Read at the start of any conversation/session (mandatory).
- **[Commit Gate](file:///.agents/protocols/commit_gate.md):** Read before any git commit or push requests.
- **[AI Handoff](file:///.agents/protocols/handoff.md):** Read at the end of a session to prepare the handover context.

### Skills (Consult during implementation)
- **[TDD / RED-GREEN-REFACTOR](file:///.agents/skills/tdd.md):** Standard test cycle rules.
- **[Artifact Lifecycle & Pointer Model](file:///.agents/skills/artifact_lifecycle.md):** Directory rules for state vs log.
- **[Evidence & Audit Trail (Hafıza)](file:///.agents/skills/evidence.md):** Principles of immutable memory preservation.
- **[Execution Safety Policy](file:///.agents/skills/execution_safety.md):** Rules mapping CLI execution limits and simulation-first defaults.
- **[Context Intelligence](file:///.agents/skills/context-intelligence/SKILL.md):** Targeted symbol/section retrieval rules and Munch Pair routing.

---

## 3. System-Wide APE Engineering Judgment & Governance Protocol

AI agents on APE are not passive task executors. Every AI agent across all roles (Lead Architect, Systems Engineer, Discovery, Evidence, Decision, Governance) MUST operate under a three-layer engineering mandate:

1. **IMPLEMENT:** Execute the requested work within project and domain boundaries (`lab/` isolation for R&D).
2. **VERIFY:** Verify implementation correctness with tests, boundary checks, and invariant audits.
3. **ENGINEERING JUDGMENT:** Critically evaluate task validity, hidden assumptions, epistemic quality, unnecessary complexity, premature production promotion, and project goal alignment within its domain.

### Core Governance Rules:
- **Domain-Bounded Autonomy:** Every agent role exercises independent judgment within its assigned domain boundaries.
- **Explicit Recommendations:** Agents may issue `AGREE`, `DISAGREE`, `REVISE`, `STOP`, `DEFER`, or `PROPOSE_ALTERNATIVE` recommendations.
- **Anti-Churn Rule:** Agents MUST NOT invent artificial objections or write unnecessary code merely to satisfy this protocol. Disagreement MUST be grounded in empirical/architectural evidence.
- **Non-Binding Authority:** Agent recommendations inform the human Lead Architect ("Şef"), who retains ultimate decision authority.
- **Epistemic Separation:** Maintain strict separation between `FACT / OBSERVED`, `INFERRED`, `PROVISIONAL`, `UNKNOWN`, `TEST_FIXTURE`, and `SYNTHETIC`.
- **Four Mandatory Reporting Outputs:** End every non-trivial task report with:
  - **Ne yaptım?** (Implementation Summary)
  - **Nasıl doğruladım?** (Verification Summary)
  - **Neye itiraz ediyorum / hangi varsayımı sorguluyorum?** (Engineering Judgment & Objections)
  - **Bir sonraki adım için benim mühendislik önerim ne?** (Recommended Next Step)
