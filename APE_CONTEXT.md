# APE_CONTEXT.md — AUTHORITATIVE AI HANDOFF CONTEXT PACK

> ⚠️ **HANDOFF PRINCIPLE #1:**
> **"Do not trust historical chat context over repository evidence."**
> Repository source code, test suites, specs, and Git state are ALWAYS the single canonical source of truth.

---

## 1. PROJECT IDENTITY
* **Project Name:** Autonomous Production Engine (APE)
* **Purpose:** Governed, autonomous build & execution engine CLI that translates high-level topics or tasks into validated, evidence-backed software deliverables with strict human approval gates and fail-closed security boundaries.
* **Current Maturity:** Hardened Architectural Foundation / Pre-Production (Post RFC-021 + SPEC-0012 + SPEC-0016).
* **Repository:** `doriangry49-collab/ape` (`https://github.com/doriangry49-collab/ape.git`)
* **Primary Branch:** `main`

---

## 2. AUTHORITATIVE GIT STATE
* **Current Local HEAD:** `1365f6b9a57cec1227006340394c54e3df0a9f8f` (`1365f6b`)
* **Remote Main HEAD:** `1365f6b9a57cec1227006340394c54e3df0a9f8f` (`1365f6b`)
* **Sync State:** `Local main == origin/main` (100% Synchronized)
* **Working Tree:** `Clean` (`nothing to commit, working tree clean`)
* **Latest Verified Commits:**
  1. `1365f6b` — `feat: align legacy scanners with SPEC-0012 failure semantics`
  2. `193d259` — `feat: formalize execution task state machine`
  3. `a9be9b9` — `feat: establish context intelligence retrieval`
  4. `14641ec` — `feat: add governed build status observability`
  5. `087aa49` — `feat: harden execution boundaries and failure visibility`

---

## 3. ARCHITECTURAL OVERVIEW
APE architecture follows a modular, deterministic pipeline (`decide` -> `plan` -> `execute` -> `release` -> `status`):

```
                        ┌───────────────────────────────┐
                        │   Scanner / Discovery Layer   │
                        │ (HN, GitHub, Web Search, etc) │
                        └───────────────┬───────────────┘
                                        │ (Raw Signals - SPEC-0012)
                                        ▼
                        ┌───────────────────────────────┐
                        │    Research Engine & Models   │
                        └───────────────┬───────────────┘
                                        │ (.build/research/<slug>.json)
                                        ▼
                        ┌───────────────────────────────┐
                        │    Decision Engine & Gate     │
                        └───────────────┬───────────────┘
                                        │ (.build/decisions/<slug>.json)
                                        ▼
                        ┌───────────────────────────────┐
                        │    Roadmap Generator & Plan   │
                        └───────────────┬───────────────┘
                                        │ (.build/roadmaps/<slug>.json)
                                        ▼
                        ┌───────────────────────────────┐
                        │   Governed Execution Engine   │
                        │ (Task State Machine - SPEC-16)│
                        └───────────────┬───────────────┘
                                        │ (.build/execution/<slug>/current.json)
                                        ▼
                        ┌───────────────────────────────┐
                        │    Governed Release Gate      │
                        │    (Commit & Evidence Log)    │
                        └───────────────┬───────────────┘
                                        │ (.governance/evidence/release-*.jsonl)
                                        ▼
                        ┌───────────────────────────────┐
                        │ StatusService & Observability │
                        │        (ape status)           │
                        └───────────────────────────────┘
```

### Component Responsibilities:
1. **Scanner / Discovery Layer:** Collects external signals. `SPEC-0012` prohibits mock data generation; raises `AdapterError` on failure.
2. **Research Engine:** Analyzes raw market/topic signals to compute confidence scores and recommended actions.
3. **Decision Engine & Gate:** Evaluates research data, classifies `BUILD`/`VALIDATE`/`WATCH`/`IGNORE` policies via `ExecutionPolicy`.
4. **Roadmap Generator & Planner:** Generates structured execution roadmaps with milestones and tasks.
5. **Execution Engine & State Machine (`SPEC-0016`):** Executes tasks sequentially under `TaskStateMachine` controls (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `DENIED`, `BLOCKED`).
6. **Governance & Evidence System:** Preserves immutable audit trails at `.governance/evidence/<track>-YYYY-MM.jsonl`.
7. **Release Gate:** Pre-checks quality metrics, executes human approval gate, and stages/commits release.
8. **Observability (`StatusService`):** Provides pure read-only status and build history reports via `ape status`.

---

## 4. ARCHITECTURAL EVOLUTION
* **RFC-012 → RFC-014:** Decision gate foundation, decision-to-execution lineage, and policy classification.
* **RFC-015 → RFC-017:** Intelligent roadmap generation, `ApeCoderAgent` integration, Docker sandbox boundary, end-to-end `ape build`.
* **RFC-018 → RFC-019:** Governed `ReleaseGate` commit boundary, evidence hashing, quality pre-checks, user journey polish.
* **RFC-020 (`087aa49`):** Path containment security (`validate_path_containment`), agent workspace root override, fail-closed release gate.
* **RFC-021 (`14641ec`):** `StatusService` and `ape status <topic>` / `ape status --all` read-only observability.
* **Post-RFC-021 Evrimler:**
  - `a9be9b9` — Context Intelligence Protocol & Munch Pair routing guide.
  - `193d259` — `SPEC-0016`: Execution task state machine formalization and `DENIED` terminal state.
  - `1365f6b` — `SPEC-0012`: Legacy scanners error alignment (`AdapterError`, `ERROR != UNKNOWN`).

---

## 5. CURRENT CAPABILITIES
* ✅ **Autonomous Governed Build (`ape build "<topic>"`):** End-to-end pipeline execution from research to git commit.
* ✅ **Read-Only Observability (`ape status "<topic>"` & `ape status --all`):** Zero-side-effect build status inspection.
* ✅ **Path Containment Guard:** Rejects relative traversal (`../`), absolute POSIX/Windows paths, and sibling prefix escapes.
* ✅ **Terminal State Safety:** `DENIED`, `COMPLETED`, and `BLOCKED` states reject further transitions (`InvalidTransitionError`).
* ✅ **Lineage Integrity:** Carries `decision_id`, `policy_decision`, and `evidence_hash` across all execution and release events.
* ✅ **Fail-Closed Release Boundary:** Aborts release on quality pre-check failures or git status inspection errors.
* ✅ **Synthetic-Free Observation (`SPEC-0012`):** Network errors propagate `AdapterError` without mock evidence.

---

## 6. CONTRACTS & GOVERNANCE
1. **`SPEC-0012` (Observation Inference Contract):** `ERROR != UNKNOWN`. Scanner network failures MUST raise `AdapterError` rather than emitting synthetic mock evidence.
2. **`SPEC-0016` (Execution Task State Machine Contract):**
   - Canonical status Enum: `PENDING`, `IN_PROGRESS`, `REQUIRES_APPROVAL`, `COMPLETED`, `FAILED`, `DENIED`, `PAUSED`, `BLOCKED`.
   - `COMPLETED`, `DENIED`, `BLOCKED` are immutable terminal states.
   - `TaskStateMachine.deny()` transitions `REQUIRES_APPROVAL` $\rightarrow$ `DENIED`.
3. **Decision Lineage:** Execution events preserve `decision_id`, `policy_decision`, and `evidence_hash`.
4. **Append-Only Evidence:** Log files under `.governance/evidence/` are immutable append-only records.
5. **No Unapproved Git Push:** Automatic `git push` is prohibited (`REQUIRES_APPROVAL` / restricted).

---

## 7. CONTEXT INTELLIGENCE & RETRIEVAL
To minimize token consumption during repository exploration, AI agents should follow the **Context Intelligence Protocol**:

* **`jCodeMunch` (Python Symbol Retrieval):** Use symbol-level tools (`get_symbol`, `search_symbols`) for `.py` files.
* **`jDocMunch` (Document Section Retrieval):** Use section-level tools (`get_section`, `get_outline`) for `.md` and SPEC files.
* **Direct `view_file` Usage:** Restricted to files under 50 lines or creating new files.
* **No Unbounded Dump:** Reading entire codebase files into context without target line bounds is strictly discouraged.

---

## 8. TEST & VALIDATION
* **Framework:** Pytest unit test suite.
* **Last Verified Offline Test Run:** **225 passed, 2 warnings, 10 deselected** (%100 PASS).
* **Offline Command:** `pytest -m "not integration" --tb=short -q`
* **Static Check:** `ruff check src/ --select F821,F401,I001` (0 errors).
* **Format Check:** `git diff --check` (Clean).
* **Integration Isolation:** Integration tests requiring network are marked `pytest.mark.integration` and deselected by default.

---

## 9. DEVELOPMENT PROTOCOL
AI agents MUST follow this strict 8-step lifecycle when modifying APE:

```
Observe ──► Understand ──► Plan ──► Implement ──► Test ──► Verify ──► Commit ──► Push
```

1. **Observe:** Inspect repository state (`git status`) and target files.
2. **Understand:** Read relevant `docs/specs/` or `SKILL.md` documents.
3. **Plan:** Formulate exact changes without making assumptions.
4. **Implement:** Edit only target files within scope.
5. **Test:** Run relevant pytest suites.
6. **Verify:** Run static checks (`ruff check`, `git diff --check`).
7. **Commit:** Stage target files and commit **(Requires Chief approval)**.
8. **Push:** Push to GitHub origin main **(Requires Chief approval)**.

---

## 10. MULTI-AGENT PROTOCOL
To support multi-agent collaboration:

* **Antigravity (Primary Implementation Agent):** Responsible for primary feature development, refactoring, and initial test writing.
* **Codex (Secondary Engineer & Reviewer):** Responsible for second-eye audits, security reviews, test adequacy verification, and secondary implementation.
* **Write Collision Rule:** **No two AI agents may write to or modify the same file simultaneously.**

---

## 11. EXPLICIT TOOL BOUNDARIES
* **ZCode:** **ZCode is NOT part of the APE workflow.** Do NOT treat ZCode as a default team member or tool.
* **Zerger:** Zerger is ONLY a reference or inspiration source when explicitly relevant; it is NOT a default development tool.
* **Antigravity:** Primary active development environment.
* **Codex:** Secondary controlled engineer / audit agent.

---

## 12. CURRENT STATUS
* **Git Status:** 100% clean and synchronized with `origin/main` at commit `1365f6b`.
* **Architecture:** Stable pre-production foundation with hardened execution boundaries, task state machine, read-only status observability, and honest scanner error handling.

---

## 13. NEXT DEVELOPMENT OBJECTIVE (CANDIDATE)
* **Candidate Next Objective — subject to Chief approval:**
  `RFC-022: Semantic Deliverable & Content Verification Gate`
  *(Extends DeliverableVerifier beyond simple file existence to include semantic content correctness and quality metric validation).*

---

## 14. HANDOFF RULES
1. **Repository Evidence Over Chat Context:** Always verify claims against actual files and test executions.
2. **Read-Only First:** Never mutate codebase or git state during inspection or planning phases.
3. **Fail-Closed Default:** Any security or governance ambiguity defaults to blocking execution.

---

## 15. QUICK START FOR NEW AI
When taking over the APE repository, execute these 10 steps first:

1. Verify working tree is clean: `git status`
2. Check local and remote HEAD alignment: `git rev-parse HEAD` & `git rev-parse origin/main`
3. Read `START_HERE_AI.md`
4. Read `.agents/skills/context-intelligence/SKILL.md`
5. Execute offline test suite: `pytest -m "not integration" --tb=short -q`
6. Run static linter: `ruff check src/ --select F821,F401,I001`
7. Check workspace build status: `ape status --all`
8. Inspect CLI entry point in `src/ape/cli.py`
9. Read target specification in `docs/specs/` (e.g. `SPEC-0016`)
10. Formulate implementation plan before modifying any code.

---

## 16. CRITICAL FACTS
1. `TaskStatus.DENIED` is a terminal state; redden/denied tasks cannot be re-executed (`SPEC-0016`).
2. `ERROR != UNKNOWN` (`SPEC-0012`): Scanner network failures raise `AdapterError` without mock evidence.
3. Automatic `git push` is strictly prohibited without explicit user approval.
4. `validate_path_containment()` prevents target paths from escaping project root.
5. Log files under `.governance/evidence/` are append-only and immutable.
6. `StatusService` is strictly read-only and opens files only in `"r"` mode.
7. `ExecutionEngine` preserves decision lineage (`decision_id`, `evidence_hash`) on all tasks.
8. Lineage mismatches trigger an explicit `⚠️ LINEAGE MISMATCH` warning in `ape status`.
9. Docker sandbox absence triggers a fail-closed `BLOCKED` state.
10. `jCodeMunch` inspects Python symbols; `jDocMunch` inspects Markdown sections.
11. `ReleaseGate` fails closed on quality pre-check failures or git status errors.
12. `slugify` strips path traversal characters (`.`, `/`, `\`, `:`), preventing path escape via topic names.
13. `APE_CONTEXT.md` is the authoritative handoff documentation for AI agents.
14. Repository evidence ALWAYS overrides historical chat assumptions.

---

## 17. KNOWN RISKS / OPEN QUESTIONS
* **Risk 1 (Docker Dependency):** Execution sandbox relies on Docker availability. In environments without Docker, sandbox tasks fail-closed to `BLOCKED`.
* **Open Question 1 (Semantic Verification):** Deliverable verification currently validates file existence and basic quality pre-checks; deep semantic validation is candidate `RFC-022`.

---

*Document Purpose: Authoritative AI Handoff Context Pack for APE.*
