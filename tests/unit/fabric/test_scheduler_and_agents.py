"""
Unit tests for Agent Scheduler and Reference Agents (PR-A3 / PR-A6).
"""

from pathlib import Path
import pytest

from ape.fabric.agents import PlannerAgent, QAAgent, ReleaseAgent
from ape.fabric.memory import SharedMemoryWorkspace
from ape.fabric.registry import AgentRegistry
from ape.fabric.scheduler import AgentScheduler


def test_reference_agents_and_scheduler_flow(tmp_path: Path):
    registry = AgentRegistry()
    planner = PlannerAgent()
    qa = QAAgent()
    release = ReleaseAgent()

    registry.register_agent("planner", planner)
    registry.register_agent("qa", qa)
    registry.register_agent("release", release)

    scheduler = AgentScheduler(registry=registry)
    workspace = SharedMemoryWorkspace("calc_app", project_root=tmp_path)

    reports = scheduler.schedule_sequence(["planner", "qa", "release"], workspace)

    assert len(reports) == 3
    assert reports[0].agent_name == "ape_planner_agent"
    assert reports[1].agent_name == "ape_qa_agent"
    assert reports[2].agent_name == "ape_release_agent"
    assert workspace.get("release_verdict") in ("APPROVED", "REJECTED")
