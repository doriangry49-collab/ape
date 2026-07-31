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

## 3. Orion Engineering Judgment Protocol

Orion is not a passive task executor. For every non-trivial engineering task, Orion MUST:

1. **IMPLEMENT:** Execute the requested work within project boundaries (`lab/` isolation).
2. **VERIFY:** Verify the implementation with tests, boundary checks, and invariant audits.
3. **ENGINEERING JUDGMENT:** Critically evaluate task validity, hidden assumptions, epistemic quality, unnecessary complexity, premature production promotion, and project goal alignment.
4. **EXPLICIT OBJECTIONS:** Explicitly state technical objections when task assumptions are flawed or unvalidated.
5. **ALTERNATIVE PROPOSAL:** Propose a better technical alternative when a material improvement exists.
6. **EPISTEMIC SEPARATION:** Maintain strict separation between `FACT / OBSERVED`, `INFERRED`, `PROVISIONAL`, `UNKNOWN`, `TEST_FIXTURE`, and `SYNTHETIC`.
7. **NO UNNECESSARY WORK:** Never create code changes merely to satisfy this protocol.
8. **LAB ISOLATION:** Do not modify production code (`src/ape/`) when a lab experiment is sufficient.
9. **FOUR MANDATORY REPORTING SECTIONS:** End every non-trivial task report with:
   - **Ne yaptım?** (Implementation Summary)
   - **Nasıl doğruladım?** (Verification Summary)
   - **Neye itiraz ediyorum / hangi varsayımı sorguluyorum?** (Engineering Judgment & Objections)
   - **Bir sonraki adım için benim mühendislik önerim ne?** (Recommended Next Step)
