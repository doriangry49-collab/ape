"""
APE Agent Fabric Subsystem — RFC-022 / PR-A1 to PR-A6 Specification.
"""

from ape.fabric.bus import FabricEvent, ObservationBus, get_default_observation_bus
from ape.fabric.contracts import AgentReport, ApeAgent
from ape.fabric.loader import AgentLoader
from ape.fabric.manifest import AgentManifest
from ape.fabric.memory import SharedMemoryWorkspace
from ape.fabric.registry import AgentRegistry, get_default_agent_registry
from ape.fabric.scheduler import AgentScheduler
from ape.fabric.state import AgentLifecycle, AgentStatus, InvalidAgentTransitionError

__all__ = [
    "ApeAgent",
    "AgentReport",
    "AgentManifest",
    "AgentRegistry",
    "get_default_agent_registry",
    "AgentStatus",
    "AgentLifecycle",
    "InvalidAgentTransitionError",
    "AgentLoader",
    "SharedMemoryWorkspace",
    "FabricEvent",
    "ObservationBus",
    "get_default_observation_bus",
    "AgentScheduler",
]
