"""Product Proof Campaign v0.1 End-to-End Verification Test Suite.

Verifies the 4 core campaign scenarios specified in PRODUCT_PROOF.md:
1. Scenario 1: Full Governed Autonomous Build (BUILD Policy)
2. Scenario 2: Fast-Fail Policy Gate (WATCH / BLOCKED Policy)
3. Scenario 3: Capability Missing Fast-Fail (MISSING_CAPABILITY)
4. Scenario 4: Verification Failure & Fail-Closed Guard (MISSING_DELIVERABLES)
"""

import json
from pathlib import Path

import pytest

from ape.intelligence.execution.engine import ExecutionEngine, PolicyExecutionBlockedError
from ape.pipeline.contracts import ExecutionContext, StageStatus
from ape.pipeline.runner import ConstitutionalPipelineRunner, PipelineExecutionError
from ape.pipeline.stages.capability_check import CapabilityCheckStage, LocalCapabilityProvider
from ape.pipeline.stages.execution_evidence import ExecutionEvidenceStage
from ape.pipeline.stages.execution_persist import ExecutionPersistStage
from ape.pipeline.stages.execution_plan import ExecutionPlanStage
from ape.pipeline.stages.policy_gate import PolicyGateStage
from ape.pipeline.stages.release_decision import ReleaseDecisionStage
from ape.pipeline.stages.task_execution import TaskExecutionStage
from ape.pipeline.stages.verification import VerificationStage


def _setup_workspace(tmp_path: Path, topic_slug: str, decision: str = "BUILD", tasks=None):
    """Helper to set up a governed workspace with decision and roadmap artifacts."""
    # 1. Decision artifact
    decisions_dir = tmp_path / ".build" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    decision_data = {
        "decision_id": f"dec_{topic_slug}",
        "decision": decision,
        "policy": f"{decision}_NOW",
        "evidence_hash": f"sha256_{topic_slug}_hash",
        "score": 85,
        "reason": "Strong market demand and low risk",
    }
    (decisions_dir / f"{topic_slug}.json").write_text(
        json.dumps(decision_data), encoding="utf-8"
    )

    # 2. Roadmap artifact
    roadmaps_dir = tmp_path / ".build" / "roadmaps"
    roadmaps_dir.mkdir(parents=True, exist_ok=True)
    default_tasks = [
        {
            "task_id": "t1",
            "description": "Create application entrypoint",
            "deliverables": ["main.py"],
            "action": "create_file",
        }
    ]
    roadmap_data = {
        "roadmap_id": f"rm_{topic_slug}",
        "decision_id": f"dec_{topic_slug}",
        "goal": f"Build {topic_slug}",
        "milestones": [{"tasks": tasks if tasks is not None else default_tasks}],
    }
    (roadmaps_dir / f"{topic_slug}.json").write_text(
        json.dumps(roadmap_data), encoding="utf-8"
    )

    return tmp_path


def test_scenario_1_full_governed_autonomous_build(tmp_path: Path):
    """Scenario 1: Full Governed Autonomous Build (BUILD Policy)."""
    topic_slug = "microservice_ledger"
    _setup_workspace(tmp_path, topic_slug, decision="BUILD")

    # Create declared deliverable file to satisfy verification
    (tmp_path / "main.py").write_text("# Ledger API Entrypoint\n", encoding="utf-8")

    engine = ExecutionEngine(tmp_path, dry_run=True)
    summary = engine.execute("Microservice Ledger API", topic_slug)

    assert "t1" in summary["executed"]

    # Verify state and evidence persistence
    state_file = tmp_path / ".build" / "execution" / topic_slug / "current.json"
    assert state_file.exists()
    state_data = json.loads(state_file.read_text(encoding="utf-8"))
    assert state_data["status"] == "COMPLETED"
    assert state_data["decision_id"] == f"dec_{topic_slug}"

    # Verify governance evidence append-only log
    evidence_dir = tmp_path / ".governance" / "evidence"
    assert evidence_dir.exists()
    log_files = list(evidence_dir.glob("execution-*.jsonl"))
    assert len(log_files) > 0


def test_scenario_2_fast_fail_policy_gate_watch(tmp_path: Path):
    """Scenario 2: Fast-Fail Policy Gate (WATCH / BLOCKED Policy)."""
    topic_slug = "high_risk_migration"
    _setup_workspace(tmp_path, topic_slug, decision="WATCH")

    engine = ExecutionEngine(tmp_path, dry_run=True)

    with pytest.raises(PolicyExecutionBlockedError) as exc_info:
        engine.execute("High Risk Migration", topic_slug)

    assert "Execution blocked: PolicyDecision is 'WATCH'" in str(exc_info.value)

    # Verify no execution state file was created
    state_file = tmp_path / ".build" / "execution" / topic_slug / "current.json"
    assert not state_file.exists()


def test_scenario_3_capability_missing_fast_fail(tmp_path: Path):
    """Scenario 3: Capability Missing Fast-Fail (MISSING_CAPABILITY)."""
    topic_slug = "containerized_app"
    _setup_workspace(tmp_path, topic_slug, decision="BUILD", tasks=[
        {"task_id": "c1", "description": "Deploy to container", "action": "deploy"}
    ])

    # Mock CapabilityProvider with missing required docker capability in live mode
    class MissingDockerProvider(LocalCapabilityProvider):
        def collect(self, tasks, dry_run=True):
            res = super().collect(tasks, dry_run=dry_run)
            res["missing_capabilities"] = ["docker"]
            return res

    stage = CapabilityCheckStage(tmp_path, provider=MissingDockerProvider(tmp_path))
    ctx = ExecutionContext(run_id="run-cap-fail", topic_slug=topic_slug, dry_run=False)

    res = stage.execute(ctx, [])
    assert res.status == StageStatus.BLOCKED
    assert res.evidence["blocked_reason"]["code"] == "MISSING_CAPABILITY"
    assert res.evidence["blocked_reason"]["retryable"] is True


def test_scenario_4_verification_failure_guard(tmp_path: Path):
    """Scenario 4: Verification Failure & Fail-Closed Guard (MISSING_DELIVERABLES)."""
    topic_slug = "missing_deliverable_app"
    _setup_workspace(tmp_path, topic_slug, decision="BUILD", tasks=[
        {"task_id": "f1", "description": "Create missing file", "deliverables": ["non_existent_file.py"], "action": "create_file"}
    ])

    # In live mode (dry_run=False), missing file causes verification failure
    ctx = ExecutionContext(run_id="run-ver-fail", topic_slug=topic_slug, dry_run=False)
    class NoOpExecutor:
        def execute(self, description, deliverables, **kwargs):
            pass
        def execute_command(self, cmd, **kwargs):
            class Dummy:
                exit_code = 0
                output = ""
                error = ""
            return Dummy()

    runner = ConstitutionalPipelineRunner([
        ExecutionPlanStage(tmp_path),
        PolicyGateStage(tmp_path),
        CapabilityCheckStage(tmp_path),
        TaskExecutionStage(tmp_path, executor=NoOpExecutor()),
        VerificationStage(tmp_path),
        ExecutionEvidenceStage(),
        ExecutionPersistStage(tmp_path),
        ReleaseDecisionStage(),
    ])

    with pytest.raises(PipelineExecutionError) as exc_info:
        runner.run(ctx)

    assert "stage 'verification'" in str(exc_info.value)
    assert "MISSING_DELIVERABLES" in str(exc_info.value) or "Missing deliverables" in str(exc_info.value)
