"""
SwarmOrchestrator & In-Memory Swarm Runtime — ORION-116 Specification.
Orchestrates single-process multi-agent swarm collaboration (Architect, Coder, QA, Auditor) using SwarmMessageBus and SharedSwarmMemory.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional

from ape.capabilities import CapabilityBroker, ExecutionContext, ExecutionRequest
from ape.fabric.agent_node import (
    AgentNode,
    AgentResponse,
    AgentRole,
    ArchitectAgentNode,
    AuditorAgentNode,
    CoderAgentNode,
    QAAgentNode,
    SwarmTask,
)
from ape.fabric.message_bus import SwarmMessage, SwarmMessageBus
from ape.fabric.shared_memory import SharedSwarmMemory


@dataclass(frozen=True)
class SwarmOutcome:
    """Immutable outcome payload produced by SwarmOrchestrator."""
    goal: str
    success: bool
    agent_responses: List[AgentResponse] = field(default_factory=list)
    memory_snapshot: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


class SwarmOrchestrator:
    """Single-process in-memory Multi-Agent Swarm Orchestrator coordinating Architect, Coder, QA, and Auditor nodes."""

    def __init__(
        self,
        capability_broker: Optional[CapabilityBroker] = None,
        message_bus: Optional[SwarmMessageBus] = None,
        shared_memory: Optional[SharedSwarmMemory] = None,
    ) -> None:
        self.capability_broker = capability_broker or CapabilityBroker()
        self.message_bus = message_bus or SwarmMessageBus()
        self.shared_memory = shared_memory or SharedSwarmMemory()

        self._agents: Dict[AgentRole, AgentNode] = {
            AgentRole.ARCHITECT: ArchitectAgentNode(),
            AgentRole.CODER: CoderAgentNode(),
            AgentRole.QA: QAAgentNode(),
            AgentRole.AUDITOR: AuditorAgentNode(),
        }

    def register_agent(self, agent_node: AgentNode) -> None:
        """Register a custom AgentNode for a specific role."""
        self._agents[agent_node.role] = agent_node

    def execute_swarm_goal(self, goal: str, context: Optional[ExecutionContext] = None) -> SwarmOutcome:
        """Execute a goal sequentially across Architect -> Coder -> QA -> Auditor swarm agent nodes."""
        start_time = time.time()
        responses: List[AgentResponse] = []

        execution_sequence = [AgentRole.ARCHITECT, AgentRole.CODER, AgentRole.QA, AgentRole.AUDITOR]

        for role in execution_sequence:
            agent = self._agents[role]
            task = SwarmTask(
                task_id=f"task_{role.value}_{int(time.time())}",
                goal=goal,
                target_role=role,
            )

            # Publish task dispatch event
            self.message_bus.publish(
                SwarmMessage(
                    message_id=f"msg_start_{role.value}",
                    sender_id="orchestrator",
                    recipient_id=agent.agent_id,
                    topic="swarm.task.started",
                    payload={"goal": goal, "role": role.value},
                )
            )

            res = agent.execute_task(task, self.shared_memory)
            responses.append(res)

            # Publish task completion event
            self.message_bus.publish(
                SwarmMessage(
                    message_id=f"msg_completed_{role.value}",
                    sender_id=agent.agent_id,
                    recipient_id="orchestrator",
                    topic="swarm.task.completed",
                    payload={"output": res.output_text, "success": res.success},
                )
            )

            if not res.success:
                dur_ms = round((time.time() - start_time) * 1000.0, 2)
                return SwarmOutcome(
                    goal=goal,
                    success=False,
                    agent_responses=responses,
                    memory_snapshot=self.shared_memory.snapshot(),
                    duration_ms=dur_ms,
                )

        dur_ms = round((time.time() - start_time) * 1000.0, 2)
        return SwarmOutcome(
            goal=goal,
            success=True,
            agent_responses=responses,
            memory_snapshot=self.shared_memory.snapshot(),
            duration_ms=dur_ms,
        )
