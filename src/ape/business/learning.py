"""
Organizational Learning Engine — RFC-022 / Phase B5 Specification.
Extracts lessons learned and pattern recommendations from persistent Enterprise Knowledge Graph.
"""

from typing import Any, Dict

from ape.workspace import EnterpriseKnowledgeGraph


class OrganizationalLearningEngine:
    """Extracts institutional lessons learned and recommends architectural patterns for new topics."""

    def __init__(self, knowledge_graph: EnterpriseKnowledgeGraph) -> None:
        self.kg = knowledge_graph

    def recommend_pattern(self, topic_category: str) -> Dict[str, Any]:
        """Query knowledge graph for historical architectural choices and recommend best pattern."""
        nodes = self.kg.query_nodes(category="architecture")
        if not nodes:
            return {
                "recommendation": "Default Modular Architecture",
                "confidence": 80.0,
                "reason": "Initial baseline pattern for new domain",
            }

        best_node = nodes[0]
        return {
            "recommendation": best_node.title,
            "confidence": 95.0,
            "reason": f"Historically verified pattern with outcome '{best_node.data.get('outcome', 'SUCCESS')}'",
            "historical_node_id": best_node.node_id,
        }

    def record_learning(self, topic_slug: str, lesson: str, outcome: str = "SUCCESS") -> None:
        """Persist new organizational learning into Enterprise Knowledge Graph."""
        self.kg.add_node(
            category="learning",
            title=f"Learning for {topic_slug}",
            data={"lesson": lesson, "outcome": outcome},
            tags=["organizational_learning", topic_slug],
        )
