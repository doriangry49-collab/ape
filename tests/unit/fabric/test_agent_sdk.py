"""
Unit tests for Agent Fabric SDK Core (PR-A1).
"""


from ape.fabric.contracts import AgentReport, ApeAgent
from ape.fabric.registry import AgentRegistry


class MockAgent:
    role = "coder"
    capabilities = ["python_code_gen"]

    @property
    def name(self) -> str:
        return "mock_coder"

    def execute(self, ctx):
        return AgentReport(agent_name=self.name, role=self.role, status="COMPLETED")

    def explain(self) -> str:
        return "Mock Coder Agent"

    def observe(self, event):
        pass

    def report(self):
        return AgentReport(agent_name=self.name, role=self.role, status="COMPLETED")


def test_agent_protocol_compliance():
    agent = MockAgent()
    assert isinstance(agent, ApeAgent)
    assert agent.role == "coder"
    assert agent.name == "mock_coder"


def test_agent_registry_resolution():
    registry = AgentRegistry()
    agent = MockAgent()
    registry.register_agent("coder", agent)

    resolved = registry.get_agents_for_role("coder")
    assert len(resolved) == 1
    assert resolved[0].name == "mock_coder"
