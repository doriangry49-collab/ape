"""
Unit tests for Agent Lifecycle State Machine (PR-A2).
"""

import pytest

from ape.fabric.state import AgentLifecycle, AgentStatus, InvalidAgentTransitionError


def test_valid_lifecycle_transitions():
    lc = AgentLifecycle(agent_name="planner_01", role="planner")
    assert lc.status == AgentStatus.IDLE

    lc.transition_to(AgentStatus.ASSIGNED)
    assert lc.status == AgentStatus.ASSIGNED

    lc.transition_to(AgentStatus.EXECUTING)
    assert lc.status == AgentStatus.EXECUTING

    lc.transition_to(AgentStatus.COMPLETED)
    assert lc.status == AgentStatus.COMPLETED


def test_invalid_lifecycle_transition_rejection():
    lc = AgentLifecycle(agent_name="planner_01", role="planner")
    with pytest.raises(InvalidAgentTransitionError, match="cannot transition from IDLE to COMPLETED"):
        lc.transition_to(AgentStatus.COMPLETED)
