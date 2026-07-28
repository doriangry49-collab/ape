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
