"""
RFC-019 Real User Journey & Governed Autonomous Build Acceptance Tests.
(RFC-019)
"""
import json
import sys
import subprocess
from pathlib import Path
import pytest
from typer.testing import CliRunner

from ape.cli import app
from ape.utils import get_artifact_history
from ape.intelligence.execution.engine import ExecutionEngine
from ape.intelligence.execution.agent import ApeCoderAgent
from ape.intelligence.roadmap.llm import PlannerModel

runner = CliRunner()


class MockDeterministicLLM(PlannerModel):
    """
    Deterministic LLM model for RFC-019 E2E repair loop test.
    Step 1: Propose broken implementation (causes pytest FAIL).
    Step 2: Propose fixed implementation (causes pytest PASS).
    """

    def __init__(self):
        self.call_count = 0

    def generate(self, prompt: str, system_message: str, schema: dict) -> dict:
        self.call_count += 1
        if self.call_count == 1:
            # Attempt 1: Create broken calculator.py + test_calculator.py
            return {
                "thought": "Create initial calculator implementation with intentional bug to verify repair loop.",
                "action": "create_file",
                "params": {
                    "path": "calculator.py",
                    "content": "def add(a, b):\n    return a - b  # Intentional bug for RFC-019 test\n",
                    "command": f'"{sys.executable}" -c "import pathlib; pathlib.Path(\'calculator.py\').write_text(\'def add(a, b):\\n    return a - b\\n\'); pathlib.Path(\'test_calculator.py\').write_text(\'from calculator import add\\ndef test_add():\\n    assert add(2, 3) == 5\\n\')" && "{sys.executable}" -m pytest test_calculator.py'
                }
            }
        else:
            # Attempt 2: Repair calculator.py
            return {
                "thought": "Fix subtraction bug in add function.",
                "action": "modify_file",
                "params": {
                    "path": "calculator.py",
                    "content": "def add(a, b):\n    return a + b\n",
                    "command": f'"{sys.executable}" -c "import pathlib; pathlib.Path(\'calculator.py\').write_text(\'def add(a, b):\\n    return a + b\\n\')" && "{sys.executable}" -m pytest test_calculator.py'
                }
            }


class LocalTestSandboxExecutor:
    """Executes commands in temporary workspace directory for offline E2E user journey testing."""

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute_command(self, cmd: str, cwd: str = "/workspace", timeout: int = 60, workspace_dir: str | None = None):
        proc = subprocess.run(cmd, shell=True, cwd=self._root, capture_output=True, text=True, timeout=timeout)
        class MockRes:
            pass
        res = MockRes()
        res.exit_code = proc.returncode
        res.output = proc.stdout
        res.error = proc.stderr
        res.status = "COMPLETED" if proc.returncode == 0 else "FAILED"
        return res


def test_e2e_real_user_journey_build_subcommand(tmp_path, monkeypatch):
    """
    Proves the full RFC-019 governed user journey:
    CLI build command -> Research -> Decision Gate -> Planner -> Engine -> Agent -> Sandbox -> ReleaseGate -> Git Commit.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ape").mkdir()
    (tmp_path / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    # Initialize dummy git repository
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "APE Agent"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "agent@ape.dev"], cwd=tmp_path, check=True)

    readme = tmp_path / "README.md"
    readme.write_text("# APE Workspace")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True)

    # Mock DecisionEngine to return BUILD decision and write artifact
    from ape.intelligence.decision.engine import DecisionEngine, DecisionReport
    def mock_run_decision(self, topic, slug):
        dec_dir = tmp_path / ".build" / "decisions"
        dec_dir.mkdir(parents=True, exist_ok=True)
        report_data = {
            "decision_id": "dec_journey_01",
            "research_id": "res_journey_01",
            "evidence_hash": "hash_journey_01",
            "topic": topic,
            "overall_score": 85,
            "confidence": 95,
            "decision": "BUILD",
            "policy": "BUILD_NOW",
            "vector_scores": {"demand": 85, "feasibility": 90},
            "rationale": ["High score"],
            "next_step": "Build MVP"
        }
        (dec_dir / f"{slug}.json").write_text(json.dumps(report_data, indent=2))
        return DecisionReport(
            decision_id="dec_journey_01",
            research_id="res_journey_01",
            evidence_hash="hash_journey_01",
            topic=topic,
            overall_score=85,
            confidence=95,
            decision="BUILD",
            policy="BUILD_NOW",
            vector_scores={"demand": 85, "feasibility": 90},
            rationale=["High score"],
            next_step="Build MVP"
        )
    monkeypatch.setattr(DecisionEngine, "run_decision", mock_run_decision)

    # Ensure ExecutionEngine uses ApeCoderAgent and LocalTestSandboxExecutor
    orig_exec_init = ExecutionEngine.__init__
    def mock_exec_init(self, project_root, dry_run=False, interrupt_after_tasks=None, auto_deny_approvals=False, executor=None, agent=None):
        if agent is None:
            agent = ApeCoderAgent(model=MockDeterministicLLM())
        if executor is None or not dry_run:
            executor = LocalTestSandboxExecutor(tmp_path)
        orig_exec_init(self, project_root, dry_run=dry_run, interrupt_after_tasks=interrupt_after_tasks, auto_deny_approvals=auto_deny_approvals, executor=executor, agent=agent)
    monkeypatch.setattr(ExecutionEngine, "__init__", mock_exec_init)

    # Invoke CLI ape build command
    result = runner.invoke(app, ["build", "Calculator Module", "--yes"])

    if result.exit_code != 0:
        raise AssertionError(f"Build failed with exit code {result.exit_code}.\nOutput:\n{result.output}\nException:\n{result.exception}")

    assert result.exit_code == 0
    assert "Starting governed autonomous build for: 'Calculator Module'" in result.output
    assert "Step 1/4: Evaluating Decision Gate..." in result.output
    assert "Step 2/4: Generating Execution Roadmap..." in result.output
    assert "Step 3/4: Executing Tasks via Execution Engine..." in result.output
    assert "Step 4/4: Evaluating Release Gate..." in result.output
    assert "Successfully completed governed autonomous build and committed release." in result.output

    # Verify Decision Artifact
    decision_file = tmp_path / ".build" / "decisions" / "calculator_module.json"
    assert decision_file.exists()
    decision_data = json.loads(decision_file.read_text())
    assert decision_data["policy"] in ("BUILD", "BUILD_NOW", "VALIDATE")
    decision_id = decision_data["decision_id"]

    # Verify Roadmap Artifact
    roadmap_file = tmp_path / ".build" / "roadmaps" / "calculator_module.json"
    assert roadmap_file.exists()

    # Verify Execution State Artifact
    state_file = tmp_path / ".build" / "execution" / "calculator_module" / "current.json"
    assert state_file.exists()
    state_data = json.loads(state_file.read_text())
    assert state_data["status"] == "COMPLETED"
    assert state_data["decision_id"] == decision_id

    # Verify Evidence Logs
    evidence_dir = tmp_path / ".governance" / "evidence"
    rel_log = get_artifact_history(evidence_dir, "release")
    assert rel_log.exists()

    # Verify Git Log Metadata Lineage
    git_log = subprocess.run(["git", "log", "-n", "1"], cwd=tmp_path, capture_output=True, text=True).stdout
    assert f"Decision ID: {decision_id}" in git_log
    assert "feat(execution): [calculator_module]" in git_log


def test_e2e_user_journey_halted_by_rejected_decision(tmp_path, monkeypatch):
    """
    Verifies that if Decision Engine returns non-BUILD policy (e.g. IGNORE/BLOCKED),
    ape build halts cleanly at Step 1 and does not execute roadmap or release.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".ape").mkdir()
    (tmp_path / ".ape" / "config.toml").write_text("[ape]\n", encoding="utf-8")

    # Mock DecisionEngine to return IGNORE
    from ape.intelligence.decision.engine import DecisionEngine, DecisionReport
    def mock_run_decision(self, topic, slug):
        return DecisionReport(
            decision_id="dec_rejected_01",
            research_id="res_01",
            evidence_hash="hash_01",
            topic=topic,
            overall_score=20,
            confidence=90,
            decision="REJECT",
            policy="IGNORE",
            vector_scores={},
            rationale=["Low ROI"],
            next_step="Stop"
        )
    monkeypatch.setattr(DecisionEngine, "run_decision", mock_run_decision)

    result = runner.invoke(app, ["build", "Unviable Idea", "--yes"])

    assert result.exit_code == 1
    assert "Build halted by Decision Gate: Decision 'REJECT' does not allow execution." in result.output
    # Execution state must NOT be created
    state_file = tmp_path / ".build" / "execution" / "unviable_idea" / "current.json"
    assert not state_file.exists()
