"""
Unit tests for Persistent Enterprise Knowledge Graph (PR-W5).
"""

from pathlib import Path

from ape.workspace.knowledge_graph import EnterpriseKnowledgeGraph


def test_persistent_knowledge_graph(tmp_path: Path):
    kg = EnterpriseKnowledgeGraph(tmp_path)

    # Add historical choices and learnings
    kg.add_node(
        category="architecture",
        title="Microservice REST Pattern",
        data={"outcome": "SUCCESS", "projects": ["Backend API", "Mobile App"]},
        tags=["rest", "microservices"],
    )
    kg.add_node(
        category="decision",
        title="Quality Profile STRICT Enforcement",
        data={"outcome": "SUCCESS", "confidence_min": 90.0},
        tags=["governance", "policy"],
    )

    # Query graph
    arch_nodes = kg.query_nodes(category="architecture")
    assert len(arch_nodes) == 1
    assert arch_nodes[0].title == "Microservice REST Pattern"

    # Reload from persistent database
    kg_reloaded = EnterpriseKnowledgeGraph(tmp_path)
    summary = kg_reloaded.get_summary()
    assert summary["total_nodes"] == 2
    assert summary["categories"]["architecture"] == 1
