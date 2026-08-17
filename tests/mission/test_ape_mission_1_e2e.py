"""
ORION-127 — Production Proof Gate
E2E Test: Full 8-stage Constitutional Pipeline with zero bypasses.

Rules (non-negotiable):
- No _make_runner_no_verify
- No stage removal
- No dry_run=True shortcut for quality/release
- If any gate fails → test fails → we fix it or document it

Pipeline under test:
  ExecutionPlanStage
  PolicyGateStage
  CapabilityCheckStage
  TaskExecutionStage       (SimulationTaskExecutor — FINDING-001: no Docker in env)
  VerificationStage        (QualityRunner — MUST pass quality_audit_passed=True)
  ExecutionEvidenceStage
  ExecutionPersistStage
  ReleaseDecisionStage
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

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
# The one honest runner — all 8 stages, no bypasses
# ---------------------------------------------------------------------------

def _make_full_runner(root: Path) -> ConstitutionalPipelineRunner:
    """
    Full constitutional pipeline.  Zero bypasses.
    SimulationTaskExecutor is explicitly documented as FINDING-001:
    Docker is unavailable in this environment; simulation is the local equivalent.
    """
    from tests.dummy_agent import DummyAgent
    return ConstitutionalPipelineRunner([
        ExecutionPlanStage(root),
        PolicyGateStage(root),
        CapabilityCheckStage(root),
        TaskExecutionStage(root, executor=SimulationTaskExecutor(), agent=DummyAgent()),
        VerificationStage(root),          # QualityRunner fires here
        ExecutionEvidenceStage(),
        ExecutionPersistStage(root),
        ReleaseDecisionStage(),           # Release gate fires here
    ])


# ---------------------------------------------------------------------------
# Workspace setup — copies REAL production deliverables
# ---------------------------------------------------------------------------

CSV_TASKS = [
    {
        "task_id": "csv_t1",
        "description": "Create CSV Analyzer core analysis engine module",
        "deliverables": ["deliverables/csv_analyzer/src/csv_analyzer/analyzer.py"],
        "action": "create_file",
    },
    {
        "task_id": "csv_t2",
        "description": "Create CSV Analyzer CLI entry point with summary and stats commands",
        "deliverables": ["deliverables/csv_analyzer/src/csv_analyzer/cli.py"],
        "action": "create_file",
    },
    {
        "task_id": "csv_t3",
        "description": "Create CSV Analyzer unit test suite",
        "deliverables": ["deliverables/csv_analyzer/tests/test_csv_analyzer.py"],
        "action": "create_file",
    },
    {
        "task_id": "csv_t4",
        "description": "Create README documentation for CSV Analyzer",
        "deliverables": ["deliverables/csv_analyzer/README.md"],
        "action": "create_file",
    },
]


def _setup_e2e_workspace(tmp_path: Path) -> Path:
    """
    Build an APE workspace in tmp_path with real production deliverables.
    Copies the authored csv_analyzer source tree so VerificationStage
    and QualityRunner operate on production-quality code.
    """
    topic_slug = "csv_analyzer"

    # Decision artifact
    decisions_dir = tmp_path / ".build" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    (decisions_dir / f"{topic_slug}.json").write_text(json.dumps({
        "decision_id": "dec_orion127_e2e",
        "decision": "BUILD",
        "policy": "BUILD_NOW",
        "evidence_hash": "sha256_orion127_proof",
        "score": 95,
        "reason": "ORION-127 Production Proof Gate: full E2E validation run.",
    }), encoding="utf-8")

    # Roadmap artifact
    roadmaps_dir = tmp_path / ".build" / "roadmaps"
    roadmaps_dir.mkdir(parents=True, exist_ok=True)
    (roadmaps_dir / f"{topic_slug}.json").write_text(json.dumps({
        "roadmap_id": "rm_orion127_e2e",
        "decision_id": "dec_orion127_e2e",
        "goal": "ORION-127: Full E2E production proof — CSV Analyzer under constitutional supervision",
        "milestones": [{"tasks": CSV_TASKS}],
    }), encoding="utf-8")

    # Copy real production deliverables from repository
    _repo_root = Path(__file__).resolve().parent.parent.parent
    deliverables_src = _repo_root / "deliverables" / "csv_analyzer"

    file_map = {
        "deliverables/csv_analyzer/src/csv_analyzer/analyzer.py":
            deliverables_src / "src" / "csv_analyzer" / "analyzer.py",
        "deliverables/csv_analyzer/src/csv_analyzer/cli.py":
            deliverables_src / "src" / "csv_analyzer" / "cli.py",
        "deliverables/csv_analyzer/src/csv_analyzer/__init__.py":
            deliverables_src / "src" / "csv_analyzer" / "__init__.py",
        "deliverables/csv_analyzer/tests/test_csv_analyzer.py":
            deliverables_src / "tests" / "test_csv_analyzer.py",
        "deliverables/csv_analyzer/README.md":
            deliverables_src / "README.md",
    }

    for rel_dest, src_path in file_map.items():
        target = tmp_path / rel_dest
        target.parent.mkdir(parents=True, exist_ok=True)
        if src_path.exists():
            target.write_bytes(src_path.read_bytes())

    # Copy pyproject.toml (needed by dependency validator)
    pyproject_src = deliverables_src / "pyproject.toml"
    if pyproject_src.exists():
        target = tmp_path / "deliverables" / "csv_analyzer" / "pyproject.toml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(pyproject_src.read_bytes())

    return tmp_path


# ---------------------------------------------------------------------------
# ORION-127 E2E Proof Test
# ---------------------------------------------------------------------------

class TestORION127_ProductionProofGate:
    """
    ORION-127 — Production Proof Gate.

    A single class with one baseline test and four gate-specific assertions.
    All run the COMPLETE 8-stage pipeline. No bypasses.

    FINDING-001 (documented): Docker unavailable → SimulationTaskExecutor used.
    This is the only known legitimate deviation from a fully live execution.
    """

    def _run_full_pipeline(self, tmp_path: Path):
        """Run the full 8-stage pipeline and return all StageResults."""
        root = _setup_e2e_workspace(tmp_path)
        ctx = ExecutionContext(
            run_id="orion127_e2e_proof",
            topic_slug="csv_analyzer",
            dry_run=False,
        )
        return _make_full_runner(root).run(ctx), root

    # ------------------------------------------------------------------
    # Baseline: pipeline must complete without exception
    # ------------------------------------------------------------------

    def test_e2e_pipeline_completes_without_error(self, tmp_path: Path) -> None:
        """
        PRIMARY PROOF: Full 8-stage pipeline completes without PipelineExecutionError.
        If this fails, ORION-127 is NOT satisfied.
        """
        results, _ = self._run_full_pipeline(tmp_path)
        assert results, "E2E FAILED: Pipeline returned no results."
        stage_names = [r.stage_name for r in results]
        assert "task_execution" in stage_names, "E2E FAILED: task_execution stage missing."
        assert "verification" in stage_names,   "E2E FAILED: verification stage missing."
        assert "release_decision" in stage_names, "E2E FAILED: release_decision stage missing."

    # ------------------------------------------------------------------
    # Gate 1: Quality OS — must pass with real files
    # ------------------------------------------------------------------

    def test_quality_audit_passed(self, tmp_path: Path) -> None:
        """
        GATE QUALITY: VerificationStage must report quality_audit_passed=True.
        Score must be >80. No bypass.
        """
        results, _ = self._run_full_pipeline(tmp_path)
        verification = next(r for r in results if r.stage_name == "verification")
        report = verification.output_data.get("quality_report", {})
        assert report.get("quality_audit_passed") is True, (
            f"QUALITY GATE FAILED: quality_audit_passed=False  score={report.get('overall_score')}"
        )
        assert report.get("overall_score", 0) > 80, (
            f"QUALITY GATE FAILED: score {report.get('overall_score')} <= 80"
        )

    # ------------------------------------------------------------------
    # Gate 2: Release — must be approved
    # ------------------------------------------------------------------

    def test_release_decision_approved(self, tmp_path: Path) -> None:
        """
        GATE RELEASE: ReleaseDecisionStage must approve the build.
        No bypass — this is the terminal gate of the constitutional pipeline.
        """
        results, _ = self._run_full_pipeline(tmp_path)
        release = next(r for r in results if r.stage_name == "release_decision")
        from ape.pipeline.contracts import StageStatus
        assert release.status == StageStatus.SUCCESS, (
            f"RELEASE GATE FAILED: status={release.status}  error={release.error}"
        )

    # ------------------------------------------------------------------
    # Gate 3: Evidence — governance log must exist
    # ------------------------------------------------------------------

    def test_governance_evidence_written(self, tmp_path: Path) -> None:
        """
        GATE EVIDENCE: Execution evidence JSONL must be written to .governance/evidence/.
        This is the constitutional audit trail.
        """
        results, root = self._run_full_pipeline(tmp_path)
        evidence_dir = root / ".governance" / "evidence"
        assert evidence_dir.exists(), "EVIDENCE GATE FAILED: .governance/evidence/ not created."
        log_files = list(evidence_dir.glob("execution-*.jsonl"))
        assert len(log_files) > 0, "EVIDENCE GATE FAILED: No governance evidence JSONL written."

    # ------------------------------------------------------------------
    # Gate 4: Execution state — must be COMPLETED
    # ------------------------------------------------------------------

    def test_execution_state_completed(self, tmp_path: Path) -> None:
        """
        GATE STATE: Execution state file must show status=COMPLETED.
        """
        results, root = self._run_full_pipeline(tmp_path)
        state_file = root / ".build" / "execution" / "csv_analyzer" / "current.json"
        assert state_file.exists(), "STATE GATE FAILED: Execution state file not persisted."
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state.get("status") == "COMPLETED", (
            f"STATE GATE FAILED: Expected COMPLETED, got {state.get('status')}"
        )
