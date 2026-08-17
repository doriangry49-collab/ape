"""Dummy Agent for E2E Tests to satisfy fail-closed guards."""

class MockStep:
    def __init__(self, action):
        self.action = action
        self.thought = f"mock thought for {action}"
        self.status = "COMPLETED"
        self.attempt = 1
        self.params = {}
        self.exit_code = 0
        self.stdout = "mock success"
        self.stderr = ""

class MockAgentResult:
    def __init__(self, task):
        self.status = "SUCCESS"
        self.error = None
        self.steps = [MockStep(task.action)]

class DummyAgent:
    def execute_task(self, task, **kwargs):
        executor = kwargs.get("sandbox_executor") or kwargs.get("executor")
        dry_run = kwargs.get("dry_run", False)
        workspace_root = kwargs.get("workspace_root")
        if executor:
            try:
                executor.execute(task.description, task.deliverables, workspace_root=workspace_root, dry_run=dry_run)
            except TypeError:
                executor.execute(task.description, task.deliverables)
        return MockAgentResult(task)
