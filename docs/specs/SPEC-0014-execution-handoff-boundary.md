# SPEC-0014: RFC-014 Decision-to-Execution Handoff Boundary Contract

**Status:** APPROVED & FORMALIZED  
**Author:** Antigravity (Implementation Engineer) & Lead Architect  
**Sealed:** 2026-07-29  

## 1. Overview

This specification establishes the formal contract governing the boundary between
the Policy Decision layer (RFC-013 / SPEC-0013) and the Execution layer in APE.
It defines:

- The second policy gate enforced by `ExecutionEngine` (independent of `RoadmapGenerator`)
- The audit lineage fields that MUST be carried through `Roadmap` and `ExecutionState`
- The BUILD vs. VALIDATE roadmap semantics enforced by `RoadmapGenerator`
- The lineage fields that MUST appear in every `execution.jsonl` governance event

## 2. Core Invariants

1. **Execution Policy Gate:** `ExecutionEngine.execute()` MUST read the decision
   artifact (`.build/decisions/<slug>.json`) and verify `PolicyDecision` before any
   task is loaded or executed. `WATCH`, `IGNORE`, or `BLOCKED` decisions MUST raise
   `PolicyExecutionBlockedError`. This gate fires even if `ape plan` was bypassed.

2. **No Execution Without Decision:** If no decision artifact exists for a topic slug,
   `ExecutionEngine` MUST raise `FileNotFoundError`. Execution cannot proceed without
   a verified decision.

3. **Audit Lineage Propagation:** `ExecutionState` MUST carry `decision_id`,
   `policy_decision`, and `evidence_hash` from the originating `DecisionReport`.
   These fields MUST be serialized into the state file and every governance event.

4. **Policy-Semantic Roadmap Generation:** `RoadmapGenerator` MUST generate
   policy-appropriate milestones:
   - `BUILD` → MVP development track (Design & Architecture → MVP Development → Launch & Validation)
   - `VALIDATE` → Market validation track (Problem Validation → Signal Testing → Evidence Review)

5. **Roadmap Policy Field:** `Roadmap` MUST carry a `policy_decision` field
   (`"BUILD"` or `"VALIDATE"`) so `ExecutionEngine` can read policy semantics
   from the roadmap file without re-opening the decision artifact.

6. **Governance Event Lineage:** Every event written to `.governance/evidence/execution.jsonl`
   MUST include `decision_id`, `policy_decision`, and `evidence_hash`.

## 3. Allowed / Blocked Decision Flow

```
PolicyDecision  │  RoadmapGenerator  │  ExecutionEngine
────────────────┼────────────────────┼──────────────────────────────────
BUILD           │  ✅ MVP roadmap    │  ✅ Allowed
VALIDATE        │  ✅ Validation     │  ✅ Allowed
                │     roadmap        │
WATCH           │  ❌ ValueError     │  ❌ PolicyExecutionBlockedError
IGNORE          │  ❌ ValueError     │  ❌ PolicyExecutionBlockedError
BLOCKED         │  ❌ ValueError     │  ❌ PolicyExecutionBlockedError
```

## 4. Lineage Data Flow

```
DecisionReport
  ├── decision_id        ─────────────────────────────────────┐
  ├── decision (BUILD/VALIDATE)   ──────────────────────┐     │
  └── evidence_hash      ─────────────────────────────┐ │     │
                                                       │ │     │
                          ▼                            │ │     │
Roadmap                                                │ │     │
  ├── decision_id ◄───────────────────────────────────┘ │     │
  └── policy_decision ◄───────────────────────────────┘ │     │
                                                         │     │
                          ▼                              │     │
ExecutionState                                           │     │
  ├── decision_id ◄───────────────────────────────────────────┘
  ├── policy_decision                                    │
  └── evidence_hash ◄─────────────────────────────────┘
                          │
                          ▼
execution.jsonl events
  ├── decision_id
  ├── policy_decision
  └── evidence_hash
```

## 5. Exceptions

- `PolicyExecutionBlockedError` (in `execution/exceptions.py`): raised by
  `ExecutionEngine._verify_decision_gate()` when `PolicyDecision` is not
  `BUILD` or `VALIDATE`.

- `FileNotFoundError`: raised by `ExecutionEngine._verify_decision_gate()`
  when no decision artifact exists.

## 6. Non-Goals (Deferred)

- `deny()` state machine bypass (S-4) — deferred to Execution State RFC
- `_infer_action()` heuristic action inference refactor (S-5) — deferred
- Parallel task execution — out of scope
- LLM-based task generation — out of scope
