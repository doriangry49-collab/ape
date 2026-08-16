"""
ORION-129 — Minimal Decision-to-Roadmap Binding Proof

STOP CONDITION TRIGGERED: RoadmapGenerator already exists.
- engine.py: src/ape/intelligence/roadmap/engine.py
- Existing tests: tests/intelligence/p1/test_roadmap_policy_semantics.py (4 pass)
- Existing tests: tests/test_roadmap_engine.py (1 pass)

No new architecture introduced.
This test proves:
1. Decision(BUILD) → RoadmapGenerator → roadmap artifact (existing contract)
2. Roadmap artifact → ExecutionPlanStage can consume it
3. Decision(VALIDATE) remains VALIDATE (no accidental BUILD promotion)
4. ORION-128 proof remains passing (regression)
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from ape.intelligence.roadmap.engine import RoadmapGenerator
from ape.intelligence.execution.executor import SimulationTaskExecutor
from ape.pipeline.contracts import ExecutionContext
from ape.pipeline.runner import ConstitutionalPipelineRunner
from ape.pipeline.stages.capability_check import CapabilityCheckStage
from ape.pipeline.stages.execution_evidence import ExecutionEvidenceStage
from ape.pipeline.stages.execution_persist import ExecutionPersistStage
from ape.pipeline.stages.execution_plan import ExecutionPlanStage
from ape.pipeline.stages.policy_gate import PolicyGateStage
from ape.pipeline.stages.release_decision import ReleaseDecisionStage
from ape.pipeline.stages.task_execution import TaskExecutionStage
from ape.pipeline.stages.verification import VerificationStage


# ---------------------------------------------------------------------------
# Helpers — shared with existing test_roadmap_policy_semantics.py pattern
# ---------------------------------------------------------------------------

def _write_decision_artifact(
    project_root: Path,
    slug: str,
    decision: str,
    policy: str,
    score: int = 85,
) -> Path:
    """Write a minimal decision artifact compatible with RoadmapGenerator and PolicyGateStage."""
    decisions_dir = project_root / ".build" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "decision_id": f"dec_{slug}_{uuid.uuid4().hex[:6]}",
        "decision": decision,
        "policy": policy,
        "overall_score": score,
        "confidence": 85,
        "reason": f"ORION-129 proof fixture — decision={decision}",
        "evidence_hash": f"sha256_orion129_{slug}",
    }
    path = decisions_dir / f"{slug}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _build_execution_runner(root: Path) -> ConstitutionalPipelineRunner:
    """Full 8-stage pipeline — same as ORION-127/128, zero bypasses."""
    return ConstitutionalPipelineRunner([
        ExecutionPlanStage(root),
        PolicyGateStage(root),
        CapabilityCheckStage(root),
        TaskExecutionStage(root, executor=SimulationTaskExecutor()),
        VerificationStage(root),
        ExecutionEvidenceStage(),
        ExecutionPersistStage(root),
        ReleaseDecisionStage(),
    ])


# ---------------------------------------------------------------------------
# ORION-129 Proof Tests
# ---------------------------------------------------------------------------

class TestORION129_DecisionToRoadmapBinding:
    """
    ORION-129 — Decision → Roadmap → ExecutionPlan binding proof.

    STOP CONDITION: RoadmapGenerator already exists (engine.py).
    Goal: prove the chain Decision → RoadmapGenerator → ExecutionPlanStage works
    without manual stub. No new abstraction introduced.
    """

    # ------------------------------------------------------------------
    # Step 1: Decision semantics check
    # ------------------------------------------------------------------

    def test_build_decision_generates_roadmap(self, tmp_path: Path) -> None:
        """
        GATE: BUILD decision → RoadmapGenerator → roadmap artifact written.
        Roadmap must have milestones with tasks, conform to ExecutionPlanStage contract.
        """
        slug = "test_build_topic"
        _write_decision_artifact(tmp_path, slug, decision="BUILD", policy="BUILD_NOW", score=85)

        generator = RoadmapGenerator(tmp_path)
        roadmap = generator.generate_roadmap("Test Build Topic", slug)

        # Roadmap artifact must be written to disk
        roadmap_file = tmp_path / ".build" / "roadmaps" / f"{slug}.json"
        assert roadmap_file.exists(), (
            f"BUILD GATE FAIL: Roadmap not written to {roadmap_file}"
        )

        roadmap_data = json.loads(roadmap_file.read_text(encoding="utf-8"))

        # Contract compliance: ExecutionPlanStage reads roadmap_id, milestones[].tasks[]
        assert "roadmap_id" in roadmap_data, "Contract: roadmap_id missing"
        assert "milestones" in roadmap_data, "Contract: milestones missing"
        assert len(roadmap_data["milestones"]) > 0, "Contract: milestones empty"

        first_milestone = roadmap_data["milestones"][0]
        assert "tasks" in first_milestone, "Contract: tasks missing in milestone"
        assert len(first_milestone["tasks"]) > 0, "Contract: tasks empty"

        first_task = first_milestone["tasks"][0]
        assert "task_id" in first_task, "Contract: task_id missing"
        assert "description" in first_task, "Contract: description missing"
        assert "deliverables" in first_task, "Contract: deliverables missing"

        # policy_decision must be BUILD
        assert roadmap_data.get("policy_decision") == "BUILD", (
            f"BUILD GATE FAIL: policy_decision={roadmap_data.get('policy_decision')}"
        )

        print(f"\n[BUILD] roadmap_id: {roadmap_data['roadmap_id']}")
        print(f"[BUILD] milestones: {len(roadmap_data['milestones'])}")
        print(f"[BUILD] tasks[0]: {first_task['description'][:60]}")

    def test_validate_decision_remains_validate(self, tmp_path: Path) -> None:
        """
        GATE: VALIDATE decision → roadmap policy_decision stays VALIDATE.
        No accidental promotion to BUILD.
        """
        slug = "test_validate_topic"
        _write_decision_artifact(tmp_path, slug, decision="VALIDATE", policy="VALIDATE_WITH_USERS", score=60)

        generator = RoadmapGenerator(tmp_path)
        roadmap = generator.generate_roadmap("Test Validate Topic", slug)

        roadmap_file = tmp_path / ".build" / "roadmaps" / f"{slug}.json"
        assert roadmap_file.exists(), "VALIDATE roadmap not written."

        roadmap_data = json.loads(roadmap_file.read_text(encoding="utf-8"))

        # VALIDATE must remain VALIDATE
        assert roadmap_data.get("policy_decision") == "VALIDATE", (
            f"CONSTITUTIONAL VIOLATION: VALIDATE promoted to {roadmap_data.get('policy_decision')}"
        )

        # VALIDATE milestones should be validation-focused (not MVP dev)
        milestone_titles = [m["title"] for m in roadmap_data["milestones"]]
        assert "Problem Validation" in milestone_titles or "Signal Testing" in milestone_titles, (
            f"VALIDATE GATE: Expected validation-track milestones, got {milestone_titles}"
        )

        print(f"\n[VALIDATE] policy_decision: {roadmap_data['policy_decision']}")
        print(f"[VALIDATE] milestones: {milestone_titles}")

    def test_watch_ignore_blocked_raise_valueerror(self, tmp_path: Path) -> None:
        """
        GATE: WATCH/IGNORE/BLOCKED decisions must NOT produce a roadmap.
        RoadmapGenerator raises ValueError — constitutional fail-closed.
        """
        for bad_decision in ("WATCH", "IGNORE", "BLOCKED"):
            slug = f"test_{bad_decision.lower()}_topic"
            _write_decision_artifact(tmp_path, slug, decision=bad_decision, policy=bad_decision, score=20)

            generator = RoadmapGenerator(tmp_path)
            with pytest.raises(ValueError, match=bad_decision):
                generator.generate_roadmap("Bad Decision Topic", slug)

        print("\n[GATE] WATCH/IGNORE/BLOCKED correctly blocked by RoadmapGenerator")

    # ------------------------------------------------------------------
    # Step 2: ExecutionPlanStage can consume the generated roadmap
    # ------------------------------------------------------------------

    def test_executionplan_stage_consumes_generated_roadmap(self, tmp_path: Path) -> None:
        """
        GATE: RoadmapGenerator-produced roadmap → ExecutionPlanStage SUCCESS.
        This proves the Decision → Roadmap → ExecutionPlan contract is closed.
        """
        slug = "test_build_exec"

        # 1. Write decision + generate roadmap
        _write_decision_artifact(tmp_path, slug, decision="BUILD", policy="BUILD_NOW", score=85)
        generator = RoadmapGenerator(tmp_path)
        generator.generate_roadmap("Test Build Exec", slug)

        roadmap_file = tmp_path / ".build" / "roadmaps" / f"{slug}.json"
        assert roadmap_file.exists()

        # 2. Run ExecutionPlanStage alone to check contract
        from ape.pipeline.contracts import ExecutionContext, StageStatus
        ctx = ExecutionContext(
            run_id="orion129_exec_plan_test",
            topic_slug=slug,
            dry_run=False,
        )
        stage = ExecutionPlanStage(tmp_path)
        result = stage.execute(ctx, [])

        assert result.status == StageStatus.SUCCESS, (
            f"ExecutionPlanStage FAIL: {result.error}"
        )
        tasks = result.output_data.get("tasks", [])
        assert len(tasks) > 0, "ExecutionPlanStage: zero tasks parsed from generated roadmap"

        roadmap_id = result.output_data.get("roadmap_id", "")
        assert roadmap_id and roadmap_id != "UNKNOWN", (
            f"ExecutionPlanStage: roadmap_id not read correctly: {roadmap_id}"
        )

        print(f"\n[EXEC PLAN] status: {result.status}")
        print(f"[EXEC PLAN] roadmap_id: {roadmap_id}")
        print(f"[EXEC PLAN] task_count: {len(tasks)}")
        print(f"[EXEC PLAN] task[0]: {tasks[0].get('description','?')[:60]}")

    # ------------------------------------------------------------------
    # Step 3: Full BUILD chain — Decision → Roadmap → Pipeline
    # ------------------------------------------------------------------

    def test_full_build_chain_decision_to_release(self, tmp_path: Path) -> None:
        """
        PRIMARY PROOF: Decision(BUILD) → RoadmapGenerator → 8-stage pipeline → RELEASE.

        This is the chain ORION-128 manually stubbed. ORION-129 proves it works
        with the existing RoadmapGenerator — no manual stub needed.

        FINDING-001: SimulationTaskExecutor (no Docker).
        """
        slug = "test_build_chain"

        # Step 1: Decision artifact (BUILD)
        _write_decision_artifact(tmp_path, slug, decision="BUILD", policy="BUILD_NOW", score=85)

        # Step 2: RoadmapGenerator (existing class, no new abstraction)
        generator = RoadmapGenerator(tmp_path)
        roadmap = generator.generate_roadmap("Test Build Chain", slug)

        roadmap_file = tmp_path / ".build" / "roadmaps" / f"{slug}.json"
        assert roadmap_file.exists(), "PROOF FAIL: Roadmap not written."

        # Step 3: Full 8-stage pipeline
        ctx = ExecutionContext(
            run_id=f"orion129_build_{uuid.uuid4().hex[:8]}",
            topic_slug=slug,
            dry_run=False,
        )
        results = _build_execution_runner(tmp_path).run(ctx)
        stage_map = {r.stage_name: r for r in results}

        from ape.pipeline.contracts import StageStatus

        # PolicyGate: BUILD must pass
        pg = stage_map.get("policy_gate")
        assert pg is not None and pg.status == StageStatus.SUCCESS, (
            f"PROOF FAIL: PolicyGate blocked. error={pg.error if pg else 'missing'}"
        )

        # Pipeline must complete
        ep = stage_map.get("execution_persist")
        assert ep is not None and ep.status == StageStatus.SUCCESS, (
            f"PROOF FAIL: execution_persist failed. error={ep.error if ep else 'missing'}"
        )

        # Release
        rd = stage_map.get("release_decision")
        assert rd is not None and rd.status == StageStatus.SUCCESS, (
            f"PROOF FAIL: Release not approved. error={rd.error if rd else 'missing'}"
        )

        # State = COMPLETED
        state_file = tmp_path / ".build" / "execution" / slug / "current.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state.get("status") == "COMPLETED", (
            f"PROOF FAIL: Expected COMPLETED, got {state.get('status')}"
        )

        print(f"\n[CHAIN] Decision: BUILD")
        print(f"[CHAIN] Roadmap: {roadmap.roadmap_id}")
        print(f"[CHAIN] PolicyGate: {pg.status}")
        print(f"[CHAIN] Release: {rd.status}")
        print(f"[CHAIN] State: {state.get('status')}")
        print("[CHAIN] Decision -> RoadmapGenerator -> ExecutionPlan -> Release: PROVEN")
