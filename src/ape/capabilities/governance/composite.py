"""
Composite Capability & Canonical Definition Hash Contract — ORION-119.E & 119.2 Specification.
Defines Capability-only Graph Nodes and SHA-256 Canonical definition_hash computation.
Reuses existing ExecutionGraph/ExecutionEngine runtime (NO second graph engine).
"""

import hashlib
import json
import types
from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple


@dataclass(frozen=True)
class CapabilityGraphNode:
    """Graph node referencing a Capability intent (NEVER raw tools)."""
    node_id: str
    capability_id: str
    version_constraint: Optional[str] = None
    input_mappings: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.input_mappings, dict):
            object.__setattr__(self, "input_mappings", types.MappingProxyType(dict(self.input_mappings)))


@dataclass(frozen=True)
class CompositeCapabilityDefinition:
    """
    Composite Capability specification composed of CapabilityGraphNodes.
    Enforces deep immutability and canonical SHA-256 definition_hash computation.
    """
    composite_id: str
    version: str
    nodes: Tuple[CapabilityGraphNode, ...]
    edges: Tuple[Tuple[str, str], ...]
    definition_hash: str = ""

    def __post_init__(self) -> None:
        # Convert mutable lists to immutable tuples
        if isinstance(self.nodes, list):
            object.__setattr__(self, "nodes", tuple(self.nodes))
        if isinstance(self.edges, list):
            object.__setattr__(self, "edges", tuple(tuple(e) for e in self.edges))

        # Compute canonical definition_hash if not provided (119.2: excludes definition_hash field)
        if not self.definition_hash:
            calculated_hash = CompositeCapabilityDefinition.compute_canonical_hash(
                composite_id=self.composite_id,
                version=self.version,
                nodes=self.nodes,
                edges=self.edges,
            )
            object.__setattr__(self, "definition_hash", calculated_hash)

    @staticmethod
    def compute_canonical_hash(
        composite_id: str,
        version: str,
        nodes: Tuple[CapabilityGraphNode, ...],
        edges: Tuple[Tuple[str, str], ...],
    ) -> str:
        """
        Compute SHA-256 Canonical Definition Hash.
        Excludes definition_hash field itself to prevent self-reference hashing loops (119.2).
        """
        # 1. Sort nodes by node_id alphabetically
        sorted_nodes = sorted(
            [
                {
                    "node_id": n.node_id,
                    "capability_id": n.capability_id,
                    "version_constraint": n.version_constraint or "",
                    "input_mappings": dict(n.input_mappings),
                }
                for n in nodes
            ],
            key=lambda x: x["node_id"],
        )

        # 2. Sort edges alphabetically by (source, target)
        sorted_edges = sorted([[e[0], e[1]] for e in edges], key=lambda x: (x[0], x[1]))

        # 3. Build canonical dictionary
        canonical_dict = {
            "composite_id": composite_id,
            "version": version,
            "nodes": sorted_nodes,
            "edges": sorted_edges,
        }

        # 4. UTF-8 Canonical JSON Serialization & SHA-256
        canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
