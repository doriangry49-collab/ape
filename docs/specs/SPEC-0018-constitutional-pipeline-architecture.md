# SPEC-0018: Constitutional Pipeline Architecture

**Status:** PROPOSED & FORMALIZED  
**Author:** Lead Architect & Antigravity (Implementation Engineer)  
**Sealed:** 2026-08-06  

---

## 1. Overview & Vision

This specification defines the **Constitutional Pipeline Architecture** for the Autonomous Production Engine (APE). It establishes a unified, deterministic, and evidence-driven execution model shared across both **Research** (`ResearchPipeline`) and **Execution** (`ExecutionPipeline`).

Under this architecture:
- **Engine Orchestrates, Stage Decides:** Engines are lightweight runners that execute ordered sequences of stages.
- **Every Stage Emits Evidence:** Audit trails and evidence hashes are computed and attached at stage boundaries.
- **Decoupled Contracts:** Stages communicate strictly via immutable inputs, context, and outputs without explicit knowledge of subsequent stages.
- **Constitutional Gates:** Policy, capability, security, and resource budget checks can be enforced at any stage boundary.

---

## 2. Shared Stage & Pipeline Contracts

All pipeline operations MUST adhere to the core interfaces defined in `src/ape/pipeline/contracts.py`:

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import abc

class StageStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"

@dataclass(frozen=True)
class PipelineContext:
    topic_slug: str
    run_id: str
    resource_budget: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StageResult:
    stage_name: str
    status: StageStatus
    output_data: Dict[str, Any]
    evidence: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0

class PipelineStage(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique identifier of the stage."""
        pass

    @abc.abstractmethod
    def execute(self, context: PipelineContext, previous_results: List[StageResult]) -> StageResult:
        """Executes stage logic, enforcing constitutional invariants and producing evidence."""
        pass
```

---

## 3. Pipeline Topologies

### 3.1 ResearchPipeline Topology

```text
ResearchPipeline
 ├── 1. ResearchPlanStage          (Formulates search strategy & queries)
 ├── 2. ProviderSelectionStage     (Routes request to valid providers)
 ├── 3. CapabilityValidationStage  (Checks provider observation validity - SPEC-0012)
 ├── 4. EvidenceFusionStage        (Merges & deduplicates raw findings)
 ├── 5. ExplainabilityStage        (Generates lineage & decision trace)
 └── 6. ResearchPersistStage       (Immutably saves artifact to .build/research/)
```

### 3.2 ExecutionPipeline Topology

```text
ExecutionPipeline
 ├── 1. ExecutionPlanStage         (Reads decision report & loads task tree)
 ├── 2. CapabilityCheckStage       (Validates sandbox/tool requirements)
 ├── 3. PolicyGateStage            (Enforces SPEC-0014 BUILD/VALIDATE rules)
 ├── 4. TaskExecutionStage         (Runs tasks via TaskStateMachine - SPEC-0016)
 ├── 5. ExecutionEvidenceStage      (Hashes git diffs, outputs, and runtime state)
 ├── 6. VerificationStage          (Runs automated test & lint suites)
 ├── 7. ReleaseDecisionStage       (Fail-closed pre-commit release approval)
 └── 8. ExecutionPersistStage      (Finalizes evidence logs in .governance/evidence/)
```

---

## 4. Invariants & Governance Rules

1. **Evidence Continuity:** Every `StageResult` MUST populate `evidence` containing `stage_hash`, `timestamp`, and `lineage_id`.
2. **Fail-Closed Gate Traversal:** If any Stage returns `StageStatus.FAILED` or `StageStatus.BLOCKED`, the `PipelineRunner` MUST immediately halt execution and prevent downstream stages from running.
3. **No Hidden State Mutation:** Stages MUST NOT mutate global state directly; all cross-stage communication occurs via `previous_results` and `PipelineContext`.
4. **Append-Only Governance Logging:** Upon completion or failure of each stage, the `PipelineRunner` writes a structured event to `.governance/evidence/pipeline-YYYY-MM.jsonl`.

---

## 5. Non-Goals

- Replacing existing CLI commands (`ape build`, `ape status`). Pipelines power these commands under the hood.
- Dynamic graph topology / DAG execution (Pipeline topology remains linear and deterministic for 1.0).
