"""
Agent Registry — RFC-022 / PR-A1 Specification.
Manages and resolves Fabric Agents by specialized platform roles (planner, coder, qa, security, release).
"""

from typing import Any, Dict, List, Optional
from ape.fabric.contracts import ApeAgent


class AgentRegistry:
    """Registry engine tracking and resolving Fabric Agents by platform role."""

    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, ApeAgent]] = {}

    def register_agent(self, role: str, agent: ApeAgent) -> None:
        """Register a Fabric Agent under a specialized role."""
        role_key = role.strip().lower()
        if role_key not in self._registry:
            self._registry[role_key] = {}
        agent_name = getattr(agent, "name", str(agent)).strip().lower()
        self._registry[role_key][agent_name] = agent

    def get_agents_for_role(self, role: str) -> List[ApeAgent]:
        """Return list of all registered agents for a specific platform role."""
        role_key = role.strip().lower()
        return list(self._registry.get(role_key, {}).values())

    def get_agent(self, role: str, name: str) -> Optional[ApeAgent]:
        """Fetch specific registered agent by role and name."""
        role_key = role.strip().lower()
        agent_key = name.strip().lower()
        return self._registry.get(role_key, {}).get(agent_key)

    def list_all_roles(self) -> Dict[str, List[str]]:
        """Return summary mapping of roles to registered agent names."""
        return {
            role: list(agents.keys())
            for role, agents in self._registry.items()
        }


# Global default agent registry instance
default_agent_registry = AgentRegistry()


def get_default_agent_registry() -> AgentRegistry:
    """Returns global default agent registry instance."""
    return default_agent_registry
