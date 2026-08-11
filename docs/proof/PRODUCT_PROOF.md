# Product Proof Campaign v0.1 Specification

This document defines the acceptance criteria, verification scenarios, artifact expectations, and explainability narratives for **Product Proof v0.1** of the Autonomous Production Engine (APE).

---

## 🎯 Primary Goal
To prove that `ape produce "<topic>"` operates as a fully governed, constitutional, end-to-end autonomous engine:

```text
Research Pipeline (7 Stages)
       │
       ▼
Policy Decision Gate (SPEC-0014)
       │
       ▼
Roadmap Engine (Milestones & Tasks)
       │
       ▼
Execution Pipeline (8 Stages)
       │
       ▼
Release Decision & Deliverables (APPROVED / REJECTED)
       │
       ▼
Constitutional Explainability Narrative
```

---

## 📋 Campaign Verification Scenarios

### Scenario 1: Full Governed Autonomous Build (`BUILD` Policy)
* **Command:** `ape produce "Microservice Ledger API"`
* **Policy Decision:** `BUILD`
* **Expected Pipeline Flow:**
  1. `ResearchPipeline`: Synthesizes evidence signals and computes confidence score.
  2. `PolicyGate`: Evaluates `BUILD` policy.
  3. `RoadmapEngine`: Generates structured milestones and tasks.
  4. `ExecutionPipeline`:
     - `ExecutionPlanStage`: Loads roadmap and prepares execution plan.
     - `PolicyGateStage`: Confirms `BUILD` gate passage.
     - `CapabilityCheckStage`: Verifies environment readiness (`capabilities_satisfied: true`).
     - `TaskExecutionStage`: Executes task queue with `TaskStateMachine` status tracking.
     - `VerificationStage`: Verifies all declared deliverables on disk.
     - `ExecutionEvidenceStage`: Aggregates pure `EvidenceBundle`.
     - `ExecutionPersistStage`: Writes `current.json` and appends `.governance/evidence/execution-YYYY-MM.jsonl`.
     - `ReleaseDecisionStage`: Issues `release_decision: APPROVED`.
* **Acceptance Criteria:**
  - `status`: `COMPLETED`
  - `release_decision`: `APPROVED`
  - Evidence Merkle lineage unbroken.
  - Explainability narrative produced answering: *Why, How, Which Evidence, Which Policy*.

---

### Scenario 2: Fast-Fail Policy Gate (`WATCH` / `BLOCKED` Policy)
* **Command:** `ape produce "High Risk Legacy Migration"`
* **Policy Decision:** `WATCH` or `BLOCKED`
* **Expected Pipeline Flow:**
  1. `ResearchPipeline`: Identifies high risk / low confidence signals.
  2. `PolicyGate`: Issues `WATCH` policy decision.
  3. `ExecutionPipeline`:
     - `ExecutionPlanStage`: Reads plan context.
     - `PolicyGateStage`: Fast-fails with `StageStatus.BLOCKED` and `failure_reason: POLICY_DECISION_WATCH`.
* **Acceptance Criteria:**
  - Pipeline halts immediately at `PolicyGateStage` before capability check or task execution.
  - `release_decision`: `REJECTED` / `BLOCKED`
  - Governance log records blocked event without executing code.

---

### Scenario 3: Capability Missing Fast-Fail (`MISSING_CAPABILITY`)
* **Command:** `ape produce "Containerized Microservice"` (requires Docker in live mode when Docker is absent)
* **Policy Decision:** `BUILD`
* **Expected Pipeline Flow:**
  1. `PolicyGate`: Confirms `BUILD` decision.
  2. `CapabilityCheckStage`: Identifies `missing_capabilities: ["docker"]` in non-dry-run mode.
  3. Fast-fails with `StageStatus.BLOCKED` and structured `blocked_reason`:
     - `code`: `MISSING_CAPABILITY`
     - `retryable`: `true`
* **Acceptance Criteria:**
  - Execution queue is NOT started.
  - Returns structured remediation receipt for developer/system.

---

### Scenario 4: Verification Failure & Fail-Closed Guard (`MISSING_DELIVERABLES`)
* **Command:** `ape produce "Failing Deliverable Module"`
* **Policy Decision:** `BUILD`
* **Expected Pipeline Flow:**
  1. `TaskExecutionStage`: Runs task queue.
  2. `VerificationStage`: Detects declared deliverable missing on disk.
  3. Returns `StageStatus.FAILED` with `failure_reason: MISSING_DELIVERABLES`.
  4. `ReleaseDecisionStage`: Issues `release_decision: REJECTED`.
* **Acceptance Criteria:**
  - Release status is `REJECTED`.
  - State file status is marked `FAILED`.
  - Audit log records missing deliverable evidence.

---

## 📊 Summary of Product Proof Success Indicators

| Indicator | Target | Verification Method |
| :--- | :--- | :--- |
| **End-to-End Execution** | 100% | `ape produce` executes without unhandled exceptions |
| **Policy Enforcement** | 100% | Fast-fail on `WATCH`/`BLOCKED` policies |
| **Evidence Integrity** | 100% | Merkle hash lineage across all 15 stages (7 Research + 8 Execution) |
| **State Immutability** | 100% | Immutable audit JSONL logging + mutable canonical state pointer |
| **Explainability** | 100% | Comprehensive end-to-end narrative generated |
