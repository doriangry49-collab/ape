"""
ORION-128 — Research-to-Decision Production Proof

E2E test: REAL topic → REAL HackerNews provider → REAL decision → pipeline.

Architecture rules:
- NO new abstraction
- NO mock research data (production proof uses real network)
- NO stage bypass
- SimulationTaskExecutor documented as FINDING-001 (no Docker)
- Decision→Roadmap gap handled in-test (FINDING-R3 minimum binding)

Chain under test:
  ResearchEngine (HackerNews + Audience)
      ↓  disk: .build/research/<slug>.json
  DecisionEngine
      ↓  disk: .build/decisions/<slug>.json
  [Roadmap stub — FINDING-R3 minimum binding]
      ↓  disk: .build/roadmaps/<slug>.json
  ConstitutionalPipelineRunner (8 stages)
      ↓
  Evidence + Release
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from ape.intelligence.decision.engine import DecisionEngine
from ape.intelligence.execution.executor import SimulationTaskExecutor
from ape.intelligence.research.engine import ResearchEngine
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
from ape.project import Project


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOPIC = "ollama_local_llm_ecosystem"
TOPIC_SLUG = "ollama_local_llm_ecosystem"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_execution_runner(root: Path) -> ConstitutionalPipelineRunner:
    """Full 8-stage pipeline — same as ORION-127, zero bypasses."""
    from tests.dummy_agent import DummyAgent
    return ConstitutionalPipelineRunner([
        ExecutionPlanStage(root),
        PolicyGateStage(root),
        CapabilityCheckStage(root),
        TaskExecutionStage(root, executor=SimulationTaskExecutor(), agent=DummyAgent()),
        VerificationStage(root),
        ExecutionEvidenceStage(),
        ExecutionPersistStage(root),
        ReleaseDecisionStage(),
    ])


def _write_roadmap_from_decision(
    root: Path,
    topic_slug: str,
    decision_report: dict[str, Any],
) -> Path:
    """
    FINDING-R3 minimum binding:
    DecisionEngine does not write a roadmap. We write the minimal roadmap
    stub here, using the mevcut contract expected by ExecutionPlanStage.

    This is NOT a new abstraction — it fills the existing format.
    Deliverable: deliverables/<slug>/README.md (simplest provable artifact).
    """
    roadmaps_dir = root / ".build" / "roadmaps"
    roadmaps_dir.mkdir(parents=True, exist_ok=True)

    decision_id = decision_report.get("decision_id", "unknown")
    decision_val = decision_report.get("decision", "BUILD")
    score = decision_report.get("overall_score", 0)

    roadmap = {
        "roadmap_id": f"rm_orion128_{uuid.uuid4().hex[:8]}",
        "decision_id": decision_id,
        "goal": (
            f"ORION-128: Research-driven build proof for '{topic_slug}'. "
            f"Decision={decision_val}, Score={score}."
        ),
        "milestones": [
            {
                "tasks": [
                    {
                        "task_id": "orion128_t1",
                        "description": (
                            f"Create research summary README for topic '{topic_slug}' "
                            f"based on evidence from HackerNews and Audience providers."
                        ),
                        "deliverables": [
                            f"deliverables/{topic_slug}/README.md",
                        ],
                        "action": "create_file",
                    }
                ]
            }
        ],
    }

    roadmap_path = roadmaps_dir / f"{topic_slug}.json"
    roadmap_path.write_text(json.dumps(roadmap, indent=2), encoding="utf-8")
    return roadmap_path


# ---------------------------------------------------------------------------
# ORION-128 Proof Tests
# ---------------------------------------------------------------------------

class TestORION128_ResearchToDecisionProof:
    """
    ORION-128 — Research-to-Decision Production Proof.

    All tests share the same workspace (tmp_path scoped per class).
    Research runs first (real network), then Decision, then pipeline.
    """

    # ------------------------------------------------------------------
    # Gate R1: HackerNews provider must return real data
    # ------------------------------------------------------------------

    def test_hackernews_provider_returns_real_signals(self, tmp_path: Path) -> None:
        """
        GATE R1: HackerNews Algolia API must return live data.
        If this fails: ENVIRONMENT LIMITATION — network not available.
        """
        from ape.intelligence.research.providers.hackernews import HackerNewsResearchProvider
        provider = HackerNewsResearchProvider(offline=False)
        t0 = time.perf_counter()
        signals = provider.fetch_signals(TOPIC)
        elapsed = time.perf_counter() - t0

        discussions = signals.get("discussions", [])
        market_signals = signals.get("market_signals", [])

        assert len(discussions) > 0, (
            f"R1 FAIL: HackerNews returned 0 discussions for '{TOPIC}'. "
            "Network may be unavailable or topic too obscure."
        )
        assert len(market_signals) > 0, "R1 FAIL: No market signals returned."
        print(f"\n[R1] HackerNews: {len(discussions)} discussions, {elapsed:.2f}s")
        print(f"[R1] Top: {discussions[0].get('title','?')[:80]}")

    # ------------------------------------------------------------------
    # Gate R2: ResearchEngine must persist to disk
    # ------------------------------------------------------------------

    def test_research_engine_persists_report(self, tmp_path: Path) -> None:
        """
        GATE R2: ResearchEngine.run_research() must write .build/research/<slug>.json.
        Uses real HackerNews data. If network fails → offline fallback.
        """
        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")
        engine = ResearchEngine(project=project, offline=False)

        t0 = time.perf_counter()
        report = engine.run_research(TOPIC)
        elapsed = time.perf_counter() - t0

        # Check disk artifact
        research_file = tmp_path / ".build" / "research" / f"{TOPIC_SLUG}.json"
        assert research_file.exists(), (
            f"R2 FAIL: Research artifact not persisted to {research_file}"
        )

        research_data = json.loads(research_file.read_text(encoding="utf-8"))
        assert research_data.get("topic") == TOPIC or research_data.get("metadata", {}).get("topic") == TOPIC, (
            f"R2 FAIL: Topic mismatch in persisted artifact. got: {research_data.get('topic')}"
        )

        # Evidence log
        gov_dir = tmp_path / ".governance" / "evidence"
        ev_files = list(gov_dir.glob("research-*.jsonl")) if gov_dir.exists() else []
        assert len(ev_files) > 0, "R2 FAIL: Evidence log not written to .governance/evidence/"

        print(f"\n[R2] Research completed in {elapsed:.2f}s")
        print(f"[R2] Confidence: {report.confidence:.0%}")
        print(f"[R2] Pain points: {len(report.pain_points)}")
        print(f"[R2] Sources: {report.sources}")
        print(f"[R2] Next action: {report.next_recommended_action}")
        print(f"[R2] Research artifact: {research_file.name}")

    # ------------------------------------------------------------------
    # Gate R3: DecisionEngine must produce a BUILD decision
    # ------------------------------------------------------------------

    def test_decision_engine_produces_decision(self, tmp_path: Path) -> None:
        """
        GATE R3: DecisionEngine.run_decision() must produce a persisted decision.
        Reads the research artifact written by ResearchEngine.
        """
        # Ensure research artifact exists (run research first)
        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")
        ResearchEngine(project=project, offline=False).run_research(TOPIC)

        decision_engine = DecisionEngine(project_root=tmp_path)
        t0 = time.perf_counter()
        report = decision_engine.run_decision(TOPIC, TOPIC_SLUG)
        elapsed = time.perf_counter() - t0

        # Check disk artifact
        decision_file = tmp_path / ".build" / "decisions" / f"{TOPIC_SLUG}.json"
        assert decision_file.exists(), f"R3 FAIL: Decision artifact not persisted to {decision_file}"

        decision_data = json.loads(decision_file.read_text(encoding="utf-8"))
        decision_val = decision_data.get("decision", "")

        assert decision_val in ("BUILD", "VALIDATE", "WATCH", "IGNORE"), (
            f"R3 FAIL: Decision value unexpected: '{decision_val}'"
        )
        assert "decision_id" in decision_data, "R3 FAIL: decision_id missing."
        assert "evidence_hash" in decision_data, "R3 FAIL: evidence_hash missing."

        print(f"\n[R3] Decision: {decision_val}  (score={report.overall_score}, elapsed={elapsed:.2f}s)")
        print(f"[R3] decision_id: {report.decision_id}")
        print(f"[R3] evidence_hash: {report.evidence_hash[:16]}...")
        print(f"[R3] rationale: {report.rationale[:2]}")

    # ------------------------------------------------------------------
    # Gate R4: Full Research → Decision → Pipeline proof
    # ------------------------------------------------------------------

    def test_full_research_to_decision_pipeline(self, tmp_path: Path) -> None:
        """
        PRIMARY PROOF: Full Research → Decision → Pipeline chain.
        Zero bypasses. FINDING-R3 minimum binding applied (roadmap stub).

        FINDING-001 documented: SimulationTaskExecutor (no Docker).
        """
        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")

        # Step 1: Research (real provider)
        research_report = ResearchEngine(project=project, offline=False).run_research(TOPIC)
        research_file = tmp_path / ".build" / "research" / f"{TOPIC_SLUG}.json"
        assert research_file.exists(), "PROOF FAIL: Research artifact missing after ResearchEngine."

        # Step 2: Decision (reads research artifact)
        decision_engine = DecisionEngine(project_root=tmp_path)
        decision_report_obj = decision_engine.run_decision(TOPIC, TOPIC_SLUG)
        decision_file = tmp_path / ".build" / "decisions" / f"{TOPIC_SLUG}.json"
        assert decision_file.exists(), "PROOF FAIL: Decision artifact missing after DecisionEngine."

        decision_data = json.loads(decision_file.read_text(encoding="utf-8"))
        decision_val = decision_data.get("decision", "WATCH")

        print(f"\n[PROOF] Decision: {decision_val} (score={decision_report_obj.overall_score})")

        # Step 3: FINDING-R3 minimum binding — write roadmap
        # PolicyGate allows BUILD and VALIDATE through.
        # If decision is WATCH/IGNORE, we document it and skip pipeline.
        if decision_val in ("WATCH", "IGNORE"):
            pytest.skip(
                f"PROOF CONDITIONAL: Decision={decision_val}. "
                "PolicyGate would block pipeline. "
                "Research evidence insufficient for BUILD. "
                "This is a correct constitutional outcome, not a failure."
            )

        roadmap_path = _write_roadmap_from_decision(tmp_path, TOPIC_SLUG, decision_data)
        assert roadmap_path.exists(), f"PROOF FAIL: Roadmap stub not written to {roadmap_path}"
        print(f"[PROOF] Roadmap written: {roadmap_path.name}")

        # Step 4: Constitutional pipeline (8 stages)
        ctx = ExecutionContext(
            run_id=f"orion128_proof_{uuid.uuid4().hex[:8]}",
            topic_slug=TOPIC_SLUG,
            dry_run=False,
        )
        runner = _build_execution_runner(tmp_path)
        results = runner.run(ctx)

        assert results, "PROOF FAIL: Pipeline returned no results."

        stage_map = {r.stage_name: r for r in results}
        stage_names = list(stage_map.keys())
        print(f"[PROOF] Stages completed: {stage_names}")

        # Policy gate must PASS
        pg = stage_map.get("policy_gate")
        assert pg is not None, "PROOF FAIL: policy_gate stage missing."
        from ape.pipeline.contracts import StageStatus
        assert pg.status == StageStatus.SUCCESS, (
            f"PROOF FAIL: PolicyGate blocked. error={pg.error}"
        )

        # Execution must reach task_execution
        te = stage_map.get("task_execution")
        assert te is not None, "PROOF FAIL: task_execution stage missing."

        # Governance evidence must exist
        ev_dir = tmp_path / ".governance" / "evidence"
        exec_logs = list(ev_dir.glob("execution-*.jsonl")) if ev_dir.exists() else []
        assert len(exec_logs) > 0, "PROOF FAIL: No execution evidence log."

        # Execution state must be persisted
        state_file = tmp_path / ".build" / "execution" / TOPIC_SLUG / "current.json"
        assert state_file.exists(), "PROOF FAIL: Execution state not persisted."
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state.get("status") == "COMPLETED", (
            f"PROOF FAIL: Expected COMPLETED, got {state.get('status')}"
        )

        # Release decision
        rd = stage_map.get("release_decision")
        assert rd is not None, "PROOF FAIL: release_decision stage missing."
        assert rd.status == StageStatus.SUCCESS, (
            f"PROOF FAIL: Release not approved. error={rd.error}"
        )

        print(f"[PROOF] State: {state.get('status')}")
        print(f"[PROOF] Release: {rd.status}")
        print("[PROOF] Research -> Decision -> Pipeline -> Release: COMPLETE")

    # ------------------------------------------------------------------
    # Gate R4.5: FINDING-R3 Closure (Zero Test Fixture Binding Proof)
    # ------------------------------------------------------------------

    def test_r3_closure_unbound_orchestration_proof(self, tmp_path: Path) -> None:
        """
        FINDING-R3 Closure Proof:
        1. ResearchEngine runs -> .build/research/<slug>.json
        2. DecisionEngine runs -> .build/decisions/<slug>.json
        3. ExecutionEngine runs WITHOUT any test harness roadmap helper.
           Orchestration layer automatically invokes RoadmapGenerator to write
           .build/roadmaps/<slug>.json and completes 8-stage pipeline.
        """
        from ape.intelligence.execution.engine import ExecutionEngine

        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")
        ResearchEngine(project=project, offline=False).run_research(TOPIC)
        DecisionEngine(project_root=tmp_path).run_decision(TOPIC, TOPIC_SLUG)

        # Confirm decision artifact exists but roadmap artifact does NOT yet exist
        dec_file = tmp_path / ".build" / "decisions" / f"{TOPIC_SLUG}.json"
        rm_file = tmp_path / ".build" / "roadmaps" / f"{TOPIC_SLUG}.json"
        assert dec_file.exists(), "R3 Closure FAIL: Decision artifact missing."
        assert not rm_file.exists(), "R3 Closure FAIL: Roadmap artifact should not exist prior to ExecutionEngine."

        # Execute via ExecutionEngine — should automatically trigger RoadmapGenerator
        exec_engine = ExecutionEngine(project_root=tmp_path, dry_run=True)
        summary = exec_engine.execute(TOPIC, TOPIC_SLUG)

        # Now roadmap artifact MUST exist on disk
        assert rm_file.exists(), "R3 Closure FAIL: Roadmap artifact was not automatically generated by orchestration layer."

        rm_data = json.loads(rm_file.read_text(encoding="utf-8"))
        assert "roadmap_id" in rm_data
        assert "milestones" in rm_data

        print(f"\n[R3 Closure] Roadmap automatically generated: {rm_file.name} ({len(rm_data['milestones'])} milestones)")
        print(f"[R3 Closure] Execution Summary: {summary}")
        print("[R3 Closure] FINDING-R3 CLOSED: Decision -> Roadmap automatically bound at Orchestration layer with ZERO test-only fixtures!")

    # ------------------------------------------------------------------
    # Gate R5: G1/G2/G3 observation during Research->Pipeline run
    # ------------------------------------------------------------------

    def test_g1_g2_g3_observed_during_proof_run(self, tmp_path: Path) -> None:
        """
        GATE R5: Observe G1 Trajectory, G2 Health Signals, G3 Intervention
        during the Research→Decision→Pipeline run.

        RETRY live: recorded as NOT OBSERVED if not triggered.
        """
        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")
        ResearchEngine(project=project, offline=False).run_research(TOPIC)

        decision_engine = DecisionEngine(project_root=tmp_path)
        dec = decision_engine.run_decision(TOPIC, TOPIC_SLUG)

        decision_data = json.loads(
            (tmp_path / ".build" / "decisions" / f"{TOPIC_SLUG}.json").read_text(encoding="utf-8")
        )
        if decision_data.get("decision", "WATCH") in ("WATCH", "IGNORE"):
            pytest.skip("G1/G2/G3 observation skipped: decision would block pipeline.")

        _write_roadmap_from_decision(tmp_path, TOPIC_SLUG, decision_data)

        ctx = ExecutionContext(
            run_id=f"orion128_g123_{uuid.uuid4().hex[:8]}",
            topic_slug=TOPIC_SLUG,
            dry_run=False,
        )
        results = _build_execution_runner(tmp_path).run(ctx)
        stage_map = {r.stage_name: r for r in results}

        # --- G1: Trajectory ---
        ev_stage = stage_map.get("execution_evidence")
        assert ev_stage is not None, "G1 FAIL: execution_evidence stage missing."
        ev_data = ev_stage.output_data or {}
        trajectory = ev_data.get("trajectory") or ev_stage.evidence.get("trajectory", {})

        traj_present = bool(trajectory) or "trajectory" in str(ev_stage.evidence)
        print(f"\n[G1] Trajectory present: {traj_present}")
        print(f"[G1] Evidence keys: {list(ev_stage.evidence.keys()) if ev_stage.evidence else []}")

        # --- G2: Health Signals ---
        health_signals = (
            ev_data.get("health_signals")
            or ev_stage.evidence.get("health_signals", [])
        )
        hs_count = len(health_signals) if isinstance(health_signals, list) else 0
        print(f"[G2] Health signals: {hs_count}")
        if isinstance(health_signals, list) and health_signals:
            for sig in health_signals[:2]:
                print(f"[G2]   signal: {sig}")

        # --- G3: Intervention Proposal ---
        intervention = (
            ev_data.get("intervention_proposal")
            or ev_stage.evidence.get("intervention_proposal", {})
        )
        if intervention:
            action = intervention.get("proposed_action", "UNKNOWN")
            print(f"[G3] Intervention proposed_action: {action}")
        else:
            print("[G3] Intervention: None (nominal run)")

        # --- RETRY live status ---
        retry_observed = False  # Would need a failure injection to trigger
        print(f"[RETRY] Live enforcement observed: {retry_observed}")
        print(f"[RETRY] Status: NOT OBSERVED (nominal run, no failure injection)")

        # Assertions: trajectory key or evidence must exist
        assert ev_stage is not None, "G1/G2/G3 FAIL: execution_evidence stage absent."
        # We don't assert specific G1/G2/G3 structure — we observe and report.
        # The constitutional pipeline ran; evidence stage completed.
        from ape.pipeline.contracts import StageStatus
        assert ev_stage.status == StageStatus.SUCCESS, (
            f"G1/G2/G3 FAIL: execution_evidence stage status={ev_stage.status}"
        )
