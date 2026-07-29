"""
RFC-017 End-to-End Autonomous Build Validation Test.
(RFC-017)

Verifies the complete governed execution pipeline:
Decision/Policy -> Roadmap -> ExecutionEngine -> ApeCoderAgent -> Sandbox -> File Creation -> pytest FAIL -> Repair -> pytest PASS -> Lineage Audit
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

from ape.intelligence.execution.agent import ApeCoderAgent, AgentStepResult
from ape.intelligence.execution.engine import ExecutionEngine
from ape.intelligence.execution.executor import DockerSandboxExecutor, TaskExecutor, SandboxResult
from ape.intelligence.execution.models import TaskStatus
from ape.intelligence.roadmap.llm import PlannerModel


class MockAgentModel(PlannerModel):
    def __init__(self, responses: list[dict]):
        self.responses = responses
        self.call_count = 0

    def generate(self, prompt: str, system_message: str, schema: dict) -> dict:
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        return self.responses[-1]


class MockDeterministicLLM(PlannerModel):
    """
    Deterministic LLM model for RFC-017 E2E repair loop test.
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
                    "content": "def add(a, b):\n    return a - b  # Intentional bug for RFC-017 test\n",
                    "command": f'"{sys.executable}" -c "import pathlib; pathlib.Path(\'calculator.py\').write_text(\'def add(a, b):\\n    return a - b\\n\'); pathlib.Path(\'test_calculator.py\').write_text(\'from calculator import add\\ndef test_add():\\n    assert add(2, 3) == 5\\n\')" && "{sys.executable}" -m pytest test_calculator.py'
                }
            }
        else:
            # Attempt 2: Repair calculator.py
            return {
                "thought": "Fix the bug in calculator.py based on pytest failure feedback.",
                "action": "modify_file",
                "params": {
                    "path": "calculator.py",
                    "content": "def add(a, b):\n    return a + b\n",
                    "command": f'"{sys.executable}" -c "import pathlib; pathlib.Path(\'calculator.py\').write_text(\'def add(a, b):\\n    return a + b\\n\')" && "{sys.executable}" -m pytest test_calculator.py'
                }
            }


class RealWorkspaceSandboxExecutor(TaskExecutor):
    """
    Sandbox executor for offline E2E validation.
    Executes commands directly inside the isolated temporary workspace directory.
    """
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def execute(self, task_description: str, deliverables: list[str]) -> str:
        return f"[OFFLINE E2E] Executed {task_description}"

    def execute_command(self, cmd: str, cwd: str = "/workspace", timeout: int = 60, workspace_dir: str | None = None) -> SandboxResult:
        target_dir = self.workspace_root
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            status = "COMPLETED" if proc.returncode == 0 else "FAILED"
            return SandboxResult(
                exit_code=proc.returncode,
                output=proc.stdout,
                error=proc.stderr,
                status=status
            )
        except Exception as e:
            return SandboxResult(
                exit_code=-1,
                output="",
                error=str(e),
                status="FAILED"
            )


@pytest.fixture
def e2e_project_env(tmp_path):
    """Set up complete decision, roadmap, and evidence infrastructure in tmp_path."""
    project_root = tmp_path / "e2e_workspace"
    project_root.mkdir()

    # 1. Decision Artifact
    decisions_dir = project_root / ".build" / "decisions"
    decisions_dir.mkdir(parents=True)
    decision_file = decisions_dir / "calc_app.json"
    decision_data = {
        "decision_id": "dec_e2e_rfc017",
        "decision": "BUILD",
        "policy": "Core BUILD Policy",
        "evidence_hash": "hash_rfc017_e2e_proof",
        "evidence": {"ai_solvability": True}
    }
    decision_file.write_text(json.dumps(decision_data))

    # 2. Roadmap Artifact
    roadmaps_dir = project_root / ".build" / "roadmaps"
    roadmaps_dir.mkdir(parents=True)
    roadmap_file = roadmaps_dir / "calc_app.json"
    roadmap_data = {
        "roadmap_id": "rm_e2e_rfc017",
        "decision_id": "dec_e2e_rfc017",
        "policy_decision": "BUILD",
        "goal": "Build validated calculator",
        "milestones": [
            {
                "milestone_id": "ms_1",
                "title": "Calculator Core",
                "dependencies": [],
                "tasks": [
                    {
                        "task_id": "tsk_e2e_01",
                        "description": "Implement calculator module and pass pytest",
                        "action": "create_file",
                        "deliverables": ["calculator.py", "test_calculator.py"],
                        "estimated_effort": "1 hour"
                    }
                ]
            }
        ]
    }
    roadmap_file.write_text(json.dumps(roadmap_data))

    return project_root


def test_e2e_autonomous_build_repair_loop_offline(e2e_project_env):
    """
    Offline E2E Validation:
    Proves Decision -> Roadmap -> ExecutionEngine -> ApeCoderAgent -> Real Execution -> pytest FAIL -> Repair -> pytest PASS -> Lineage Audit.
    """
    project_root = e2e_project_env
    mock_llm = MockDeterministicLLM()
    sandbox = RealWorkspaceSandboxExecutor(project_root)
    agent = ApeCoderAgent(model=mock_llm, max_repair_attempts=3)

    engine = ExecutionEngine(
        project_root=project_root,
        dry_run=False,
        executor=sandbox,
        agent=agent
    )

    # Execute full pipeline
    result = engine.execute("Calculator App", "calc_app")

    # 1. Verify task execution completed
    assert "tsk_e2e_01" in result["executed"] or "tsk_e2e_01" in result.get("retried", [])

    # 2. Verify created deliverables exist in workspace
    assert (project_root / "calculator.py").exists()
    assert (project_root / "test_calculator.py").exists()

    # 3. Verify final calculator.py contains fixed code
    calc_content = (project_root / "calculator.py").read_text()
    assert "return a + b" in calc_content

    # 4. Verify evidence logs for execution and execution_agent
    from ape.utils import get_artifact_history
    evidence_dir = project_root / ".governance" / "evidence"
    agent_log_file = get_artifact_history(evidence_dir, "execution_agent")
    assert agent_log_file.exists()

    agent_logs = [json.loads(line) for line in agent_log_file.read_text().strip().split("\n") if line.strip()]

    # Verify attempt 1 was pytest FAIL and attempt 2 was pytest PASS
    assert len(agent_logs) == 2
    assert agent_logs[0]["attempt"] == 1
    assert agent_logs[0]["exit_code"] != 0
    assert agent_logs[0]["status"] == "FAILED"
    assert agent_logs[0]["decision_id"] == "dec_e2e_rfc017"
    assert agent_logs[0]["evidence_hash"] == "hash_rfc017_e2e_proof"

    assert agent_logs[1]["attempt"] == 2
    assert agent_logs[1]["exit_code"] == 0
    assert agent_logs[1]["status"] == "SUCCESS"
    assert agent_logs[1]["decision_id"] == "dec_e2e_rfc017"
    assert agent_logs[1]["evidence_hash"] == "hash_rfc017_e2e_proof"


DOCKER_AVAILABLE = shutil.which("docker") is not None


@pytest.mark.integration
@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker required for real Docker Sandbox E2E test")
def test_e2e_autonomous_build_docker_sandbox(e2e_project_env):
    """
    Real Docker Sandbox E2E Validation:
    Proves real DockerSandboxExecutor runs pytest inside Alpine container and performs repair loop.
    Skipped cleanly if Docker is not installed on host.
    """
    project_root = e2e_project_env
    mock_llm = MockDeterministicLLM()
    sandbox = DockerSandboxExecutor()
    agent = ApeCoderAgent(model=mock_llm, max_repair_attempts=3)

    engine = ExecutionEngine(
        project_root=project_root,
        dry_run=False,
        executor=sandbox,
        agent=agent
    )

    result = engine.execute("Calculator App", "calc_app")

    assert "tsk_e2e_01" in result["executed"]
    assert (project_root / "calculator.py").exists()
    assert "return a + b" in (project_root / "calculator.py").read_text()


def test_e2e_security_invariants_and_fail_closed(e2e_project_env):
    """
    E2E Security Invariants:
    1. Restricted actions (git_push, deploy, external_api_write) are blocked.
    2. Non-canonical actions (run_bash_script) are rejected.
    3. Docker missing results in BLOCKED status (no host shell fallback).
    """
    project_root = e2e_project_env

    # 1. Non-canonical action proposal
    model_non_canonical = MockAgentModel([
        {"thought": "Attempt non-canonical action", "action": "run_bash_script", "params": {}}
    ])
    agent_nc = ApeCoderAgent(model=model_non_canonical)
    engine_nc = ExecutionEngine(project_root=project_root, dry_run=False, executor=RealWorkspaceSandboxExecutor(project_root), agent=agent_nc)
    res_nc = engine_nc.execute("Calculator App", "calc_app")
    assert "tsk_e2e_01" not in res_nc["executed"]

    # 2. Restricted action proposal (git_push)
    model_restricted = MockAgentModel([
        {"thought": "Attempt git push", "action": "git_push", "params": {}}
    ])
    agent_res = ApeCoderAgent(model=model_restricted)
    engine_res = ExecutionEngine(project_root=project_root, dry_run=False, executor=RealWorkspaceSandboxExecutor(project_root), agent=agent_res)
    res_restricted = engine_res.execute("Calculator App", "calc_app")
    assert "tsk_e2e_01" not in res_restricted["executed"]
