"""
Persistent Enterprise Knowledge Graph — RFC-022 / PR-W5 Specification.
Stores historical decision trajectories, architectural choices, and evidence lineages persistently across workspaces.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeNode:
    """Represents a persistent node in Enterprise Knowledge Graph."""
    node_id: str
    category: str  # architecture, decision, quality, learning, deliverable
    title: str
    data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "category": self.category,
            "title": self.title,
            "data": self.data,
            "tags": self.tags,
        }


class EnterpriseKnowledgeGraph:
    """Persistent Enterprise Knowledge Graph engine for institutional memory."""

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.storage_dir / "knowledge_graph.json"
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._load()

    def _load(self) -> None:
        if self.db_file.exists():
            try:
                data = json.loads(self.db_file.read_text(encoding="utf-8"))
                for nid, ndata in data.items():
                    self._nodes[nid] = KnowledgeNode(
                        node_id=nid,
                        category=ndata.get("category", "learning"),
                        title=ndata.get("title", ""),
                        data=dict(ndata.get("data", {})),
                        tags=list(ndata.get("tags", [])),
                    )
            except Exception:
                pass

    def _save(self) -> None:
        data = {nid: node.to_dict() for nid, node in self._nodes.items()}
        self.db_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_node(self, category: str, title: str, data: Dict[str, Any], tags: Optional[List[str]] = None) -> KnowledgeNode:
        """Persist a new knowledge node into knowledge graph."""
        nid = f"{category}_{len(self._nodes) + 1:04d}"
        node = KnowledgeNode(
            node_id=nid,
            category=category,
            title=title,
            data=data,
            tags=tags or [],
        )
        self._nodes[nid] = node
        self._save()
        return node

    def query_nodes(self, category: Optional[str] = None, tag: Optional[str] = None) -> List[KnowledgeNode]:
        """Query knowledge graph by category or tag."""
        results: List[KnowledgeNode] = []
        for node in self._nodes.values():
            if category and node.category.lower() != category.lower():
                continue
            if tag and tag.lower() not in [t.lower() for t in node.tags]:
                continue
            results.append(node)
        return results

    def get_summary(self) -> Dict[str, Any]:
        """Return summary metrics of knowledge graph."""
        categories: Dict[str, int] = {}
        for n in self._nodes.values():
            categories[n.category] = categories.get(n.category, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "categories": categories,
            "db_path": str(self.db_file),
        }
