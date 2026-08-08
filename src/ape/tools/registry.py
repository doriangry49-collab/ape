"""
Hierarchical Tool Registry — ORION-117.0 Specification.
Provides scoped tool discovery and registration across GLOBAL, WORKSPACE, and SESSION scopes.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple

from ape.tools.contracts import ToolNotFoundError
from ape.tools.definition import ToolDefinition


class ToolScope(str, Enum):
    """Hierarchical scope levels for Tool registration."""
    GLOBAL = "global"
    WORKSPACE = "workspace"
    SESSION = "session"


class ToolRegistry:
    """Scoped registry managing ToolDefinition entries across GLOBAL, WORKSPACE, and SESSION scopes."""

    def __init__(self) -> None:
        self._stores: Dict[ToolScope, Dict[Tuple[str, str], ToolDefinition]] = {
            ToolScope.GLOBAL: {},
            ToolScope.WORKSPACE: {},
            ToolScope.SESSION: {},
        }

    def register_tool(self, definition: ToolDefinition, scope: ToolScope = ToolScope.GLOBAL) -> None:
        """Register a ToolDefinition in the specified scope."""
        key = (definition.name, definition.version)
        self._stores[scope][key] = definition

    def resolve_tool(self, name: str, version: Optional[str] = None, scope: Optional[ToolScope] = None) -> ToolDefinition:
        """Resolve a tool by name (and optional version) across SESSION -> WORKSPACE -> GLOBAL hierarchy."""
        scopes_to_search = [scope] if scope else [ToolScope.SESSION, ToolScope.WORKSPACE, ToolScope.GLOBAL]

        for s in scopes_to_search:
            store = self._stores[s]
            if version:
                key = (name, version)
                if key in store:
                    return store[key]
            else:
                # Find highest or default matching version in this scope
                matches = [defn for (n, v), defn in store.items() if n == name]
                if matches:
                    return matches[-1]

        raise ToolNotFoundError(f"Tool '{name}' (version={version}) not found in scopes {[s.value for s in scopes_to_search]}.")

    def discover_tools(self, scope: Optional[ToolScope] = None) -> List[ToolDefinition]:
        """Discover all registered tools across specified scope or hierarchy."""
        if scope:
            return list(self._stores[scope].values())
        
        # Merge hierarchy: SESSION overrides WORKSPACE overrides GLOBAL
        result: Dict[str, ToolDefinition] = {}
        for s in [ToolScope.GLOBAL, ToolScope.WORKSPACE, ToolScope.SESSION]:
            for defn in self._stores[s].values():
                result[defn.name] = defn
        return list(result.values())
