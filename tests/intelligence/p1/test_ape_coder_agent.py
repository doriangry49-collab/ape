import pytest
from ape.intelligence.execution.agent import ApeCoderAgent
from ape.intelligence.execution.models import ExecutionTask
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


class MockSandboxExecutor:
    def __init__(self, exit_code: int = 0, output: str = "ok", error: str = ""):
        self.exit_code = exit_code
        self.output = output
        self.error = error

    def execute_command(self, cmd: str, cwd: str = "/workspace", timeout: int = 60, workspace_dir: str | None = None):
        class MockRes:
            pass
        res = MockRes()
        res.exit_code = self.exit_code
        res.output = self.output
        res.error = self.error
        res.status = "COMPLETED" if self.exit_code == 0 else "FAILED"
        return res


@pytest.fixture
def sample_task():
    return ExecutionTask(
        task_id="tsk_test_01",
        description="Implement user service",
        deliverables=["user.py"],
        action="create_file"
    )


def test_ape_coder_happy_path(sample_task):
    model = MockAgentModel([
        {
            "thought": "Create the requested file",
            "action": "create_file",
            "params": {"path": "user.py", "content": "def get_user(): pass"}
        }
    ])
    agent = ApeCoderAgent(model=model, max_repair_attempts=3)
    result = agent.execute_task(sample_task, lineage={"decision_id": "dec_123", "policy_decision": "BUILD"})

    assert result.status == "COMPLETED"
    assert result.attempts == 1
    assert len(result.steps) == 1
    assert result.steps[0].action == "create_file"
    assert result.steps[0].status == "SUCCESS"


@pytest.mark.parametrize("restricted_action", ["git_push", "deploy", "external_api_write"])
def test_ape_coder_blocks_mvp_restricted_actions(sample_task, restricted_action):
    model = MockAgentModel([
        {
            "thought": f"Attempting restricted action {restricted_action}",
            "action": restricted_action,
            "params": {}
        }
    ])
    agent = ApeCoderAgent(model=model, max_repair_attempts=2)
    result = agent.execute_task(sample_task)

    assert result.status == "FAILED"
    assert any(step.status == "BLOCKED" for step in result.steps)


@pytest.mark.parametrize("invalid_action", ["run_bash_script", "system_call", "eval", "arbitrary_cmd"])
def test_ape_coder_rejects_non_canonical_actions(sample_task, invalid_action):
    model = MockAgentModel([
        {
            "thought": "Proposing uncanonical action",
            "action": invalid_action,
            "params": {}
        }
    ])
    agent = ApeCoderAgent(model=model, max_repair_attempts=2)
    result = agent.execute_task(sample_task)

    assert result.status == "FAILED"
    assert any(step.status == "REJECTED" for step in result.steps)


def test_ape_coder_repair_loop_failure_limit(sample_task):
    # Model repeatedly returns failing command
    model = MockAgentModel([
        {"thought": "Try 1", "action": "run_tests", "params": {"command": "pytest"}},
        {"thought": "Try 2", "action": "run_tests", "params": {"command": "pytest"}},
        {"thought": "Try 3", "action": "run_tests", "params": {"command": "pytest"}},
    ])
    failing_sandbox = MockSandboxExecutor(exit_code=1, error="AssertionError: 1 != 2")

    agent = ApeCoderAgent(model=model, max_repair_attempts=3)
    result = agent.execute_task(sample_task, sandbox_executor=failing_sandbox)

    assert result.status == "FAILED"
    assert result.attempts == 3
    assert len(result.steps) == 3
    assert "failed after 3 attempts" in result.error
