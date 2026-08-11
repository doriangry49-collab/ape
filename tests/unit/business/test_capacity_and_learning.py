"""
Unit tests for Capacity Manager and Organizational Learning Engine (Phase B4 / Phase B5).
"""

from pathlib import Path

from ape.business.capacity import CapacityManager
from ape.business.learning import OrganizationalLearningEngine
from ape.workspace import EnterpriseKnowledgeGraph


def test_capacity_manager_throttling():
    mgr = CapacityManager(max_concurrent_agents=2)

    assert mgr.request_slot("agent_1") is True
    assert mgr.request_slot("agent_2") is True
    assert mgr.request_slot("agent_3") is False  # Throttled into queue

    status = mgr.get_capacity_status()
    assert status["active_agents"] == 2
    assert status["queued_agents"] == 1

    next_agent = mgr.release_slot()
    assert next_agent == "agent_3"


def test_organizational_learning_engine(tmp_path: Path):
    kg = EnterpriseKnowledgeGraph(tmp_path)
    engine = OrganizationalLearningEngine(kg)

    # Initial fallback recommendation
    rec1 = engine.recommend_pattern("e_commerce")
    assert rec1["confidence"] == 80.0

    # Record institutional learning
    engine.record_learning("e_commerce", "Verified Microservice REST Architecture", outcome="SUCCESS")
    summary = kg.get_summary()
    assert summary["total_nodes"] == 1
