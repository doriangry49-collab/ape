# SPEC-0016: Execution Engine Task State Machine & Approval Boundary Contract

**Status:** APPROVED & FORMALIZED  
**Author:** Antigravity (Implementation Engineer) & Lead Architect  
**Sealed:** 2026-07-30  

## 1. Overview

This specification establishes the formal, deterministic contract governing internal task state transitions, approval policy boundaries, and action resolution within the APE `ExecutionEngine` (RFC-016). It resolves the two architectural items explicitly deferred by `SPEC-0014`:

- **S-4 Resolution:** Formalization of `TaskStatus.DENIED` as a terminal state and elimination of the `deny()` state machine bypass.
- **S-5 Resolution:** Elimination of heuristic `_infer_action()` overrides when explicit task actions are populated.

## 2. Core Invariants

1. **State Machine Ownership:** `TaskStateMachine` in `src/ape/intelligence/execution/state.py` is the single canonical owner of all task status transitions. Direct modification of `task.status` outside `TaskStateMachine` is strictly forbidden.
2. **Terminal State Immutability:** `COMPLETED`, `DENIED`, and `BLOCKED` are terminal states. Any attempt to transition out of a terminal state MUST raise `InvalidTransitionError`.
3. **Explicit Action Authority:** If an `ExecutionTask` explicitly specifies `action`, `ExecutionEngine` MUST consume `action` directly. Heuristic inference via `_infer_action()` is restricted to a fallback when `action` is empty.
4. **Audit Lineage Preservation:** Every task status transition written to `.governance/evidence/execution-YYYY-MM.jsonl` MUST preserve `decision_id`, `policy_decision`, and `evidence_hash` from the originating `DecisionReport`.
5. **Fail-Safe Decision Gate:** SPEC-0014 Policy Gate invariants remain fully binding (`BUILD` and `VALIDATE` allowed; `WATCH`, `IGNORE`, `BLOCKED` raise `PolicyExecutionBlockedError`).

## 3. Task Status Model & DENIED State

```python
class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DENIED = "DENIED"          # S-4: Formalized terminal policy/user rejection state
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"        # Terminal system/sandbox hard stop
```

## 4. Transition Matrix

| Current Status | Event / Trigger Method | Next Status | Terminal? |
| :--- | :--- | :--- | :---: |
| **`PENDING`** | `start()` | `IN_PROGRESS` | No |
| **`PENDING`** | `request_approval()` | `REQUIRES_APPROVAL` | No |
| **`PENDING`** | `block()` | `BLOCKED` | No |
| **`IN_PROGRESS`** | `complete()` | `COMPLETED` | No |
| **`IN_PROGRESS`** | `fail()` | `FAILED` | No |
| **`IN_PROGRESS`** | `pause()` | `PAUSED` | No |
| **`IN_PROGRESS`** | `request_approval()` | `REQUIRES_APPROVAL` | No |
| **`IN_PROGRESS`** | `block()` | `BLOCKED` | No |
| **`REQUIRES_APPROVAL`** | `approve()` | `IN_PROGRESS` | No |
| **`REQUIRES_APPROVAL`** | `deny()` | `DENIED` | **YES** |
| **`FAILED`** | `retry()` | `IN_PROGRESS` | No |
| **`PAUSED`** | `resume()` | `IN_PROGRESS` | No |
| **`COMPLETED`** | *None* | *Forbidden* | **YES** |
| **`DENIED`** | *None* | *Forbidden* | **YES** |
| **`BLOCKED`** | *None* | *Forbidden* | **YES** |

Any transition not explicitly listed in the matrix MUST raise `InvalidTransitionError`.

## 5. Approval Policy Boundary (S-4)

- `deny()` MUST transition `REQUIRES_APPROVAL` $\rightarrow$ `DENIED`.
- Re-assigning `REQUIRES_APPROVAL` without state transition is eliminated.
- When `deny()` is called, `ExecutionTask.error` stores the denial reason, and `TaskStatus.DENIED` becomes terminal.
- Re-executing a `DENIED` task is forbidden and MUST raise `InvalidTransitionError`.

## 6. Action Resolution Contract (S-5)

- When `ExecutionTask` is constructed or loaded from a roadmap artifact, `task.action` is evaluated.
- If `task.action` is present and non-empty, `ExecutionEngine` MUST execute `task.action` directly.
- `_infer_action()` is executed ONLY as a deterministic fallback when `task.action` is empty or missing.

## 7. Audit Lineage & Persistence

Every task transition emitted to `.governance/evidence/execution-YYYY-MM.jsonl` MUST preserve:
- `event`: Event identifier (e.g. `task_completed`, `task_failed`, `task_denied`).
- `task_id`: Task string ID.
- `previous_status`: Originating `TaskStatus`.
- `new_status`: Resulting `TaskStatus`.
- `decision_id`: Lineage ID from `DecisionReport`.
- `policy_decision`: `BUILD` or `VALIDATE`.
- `evidence_hash`: SHA-256 hash string.

## 8. Error Semantics

- **`DENIED`:** Explicit human or policy refusal of an approval request (`TaskStatus.DENIED`).
- **`FAILED`:** Runtime execution error, task exception, or failed deliverable verification (`TaskStatus.FAILED`).
- **`BLOCKED`:** Environmental or container security hard stop (`TaskStatus.BLOCKED`).
- **`InvalidTransitionError`:** Invalid state machine transition attempt outside `_TRANSITIONS`.

## 9. Backward Compatibility

- Existing state files (`current.json`) containing legacy tasks without `status` default to `TaskStatus.PENDING`.
- Existing `ExecutionTask` instances deserialize cleanly; `TaskStatus.DENIED` is added to the enum.

## 10. Test Requirements

Unit test suite (`tests/intelligence/p1/test_execution_task_state_machine.py`) MUST assert:
1. `TaskStatus.DENIED` Enum value existence.
2. `REQUIRES_APPROVAL` $\rightarrow$ `DENIED` transition via `deny()`.
3. `DENIED` terminal state immutability (`InvalidTransitionError` on transition attempt).
4. `COMPLETED` and `BLOCKED` terminal state immutability.
5. `FAILED` $\rightarrow$ `IN_PROGRESS` via `retry()`.
6. `PAUSED` $\rightarrow$ `IN_PROGRESS` via `resume()`.
7. `REQUIRES_APPROVAL` $\rightarrow$ `IN_PROGRESS` via `approve()`.
8. Explicit `task.action` preservation without `_infer_action()` override.
9. Denial event audit lineage preservation (`decision_id`, `policy_decision`, `evidence_hash`).
