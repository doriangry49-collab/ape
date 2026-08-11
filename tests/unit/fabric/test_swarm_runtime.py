"""
Unit tests for ORION-116 In-Memory Multi-Agent Swarm Runtime.
Verifies single-process SwarmOrchestrator execution (Architect, Coder, QA, Auditor),
SwarmMessageBus in-memory pub/sub, SharedSwarmMemory state store, and custom AgentNode registration.
"""

from typing import Any

from ape.fabric import (
    AgentResponse,
    AgentRole,
    BaseAgentNode,
    SharedSwarmMemory,
    SwarmMessage,
    SwarmMessageBus,
    SwarmOrchestrator,
    SwarmOutcome,
    SwarmTask,
)


def test_swarm_orchestrator_execution():
    orchestrator = SwarmOrchestrator()
    goal = "Build a resilient Next.js 14 E-commerce Dashboard"

    outcome = orchestrator.execute_swarm_goal(goal)

    assert isinstance(outcome, SwarmOutcome)
    assert outcome.success is True
    assert outcome.goal == goal
    assert len(outcome.agent_responses) == 4

    roles_executed = [r.role for r in outcome.agent_responses]
    assert roles_executed == [AgentRole.ARCHITECT, AgentRole.CODER, AgentRole.QA, AgentRole.AUDITOR]

    assert outcome.memory_snapshot.get("task_output_architect") is not None
    assert outcome.memory_snapshot.get("task_output_coder") is not None


def test_swarm_message_bus():
    bus = SwarmMessageBus()
    received = []

    def handler(msg: SwarmMessage):
        received.append(msg)

    bus.subscribe("swarm.task.completed", handler)

    msg = SwarmMessage(
        message_id="m1",
        sender_id="coder",
        recipient_id="orchestrator",
        topic="swarm.task.completed",
        payload={"status": "ok"},
    )
    bus.publish(msg)

    assert len(received) == 1
    assert received[0].sender_id == "coder"
    assert len(bus.get_history()) == 1


def test_shared_swarm_memory():
    mem = SharedSwarmMemory()
    mem.set("arch_spec", "Microservices DAG")
    mem.set("test_count", 444)

    assert mem.get("arch_spec") == "Microservices DAG"
    assert mem.has("test_count") is True

    snap = mem.snapshot()
    assert snap["arch_spec"] == "Microservices DAG"


def test_custom_agent_registration():
    class CustomSecurityAgent(BaseAgentNode):
        def __init__(self):
            super().__init__("custom_sec", AgentRole.AUDITOR)

        def execute_task(self, task: SwarmTask, shared_memory: Any) -> AgentResponse:
            shared_memory.set("sec_audit", "PASSED")
            return AgentResponse(
                agent_id=self.agent_id,
                role=self.role,
                success=True,
                output_text="[SECURITY PASSED]",
            )

    orchestrator = SwarmOrchestrator()
    orchestrator.register_agent(CustomSecurityAgent())

    outcome = orchestrator.execute_swarm_goal("Audit infrastructure")
    assert outcome.success is True
    assert outcome.memory_snapshot.get("sec_audit") == "PASSED"
