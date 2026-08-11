"""
Agent Loader & Dynamic Discovery Engine — RFC-022 / PR-A2 Specification.
Instantiates and loads Fabric Agents into AgentRegistry.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ape.fabric.contracts import ApeAgent
from ape.fabric.registry import AgentRegistry, get_default_agent_registry
from ape.fabric.state import AgentLifecycle


class AgentLoader:
    """Instantiates, validates, and registers Fabric Agents."""

    def __init__(self, registry: Optional[AgentRegistry] = None) -> None:
        self.registry = registry or get_default_agent_registry()
        self.lifecycles: Dict[str, AgentLifecycle] = {}

    def load_agent(self, agent_cls_or_obj: Any) -> ApeAgent:
        """Instantiate agent and register in registry."""
        agent = agent_cls_or_obj() if isinstance(agent_cls_or_obj, type) else agent_cls_or_obj

        role = getattr(agent, "role", None)
        name = getattr(agent, "name", None)

        if not role or not name:
            raise ValueError(f"Object {agent} must define 'role' and 'name' properties")

        self.registry.register_agent(role, agent)
        self.lifecycles[name] = AgentLifecycle(agent_name=name, role=role)
        return agent
