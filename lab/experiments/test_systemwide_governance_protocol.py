import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from lab.candidates.systemwide_governance import SystemWideGovernanceAuditor


@pytest.fixture
def auditor():
    return SystemWideGovernanceAuditor()


def test_systemwide_scope_covers_all_roles(auditor):
    """1. System-wide protocol covers all agent roles."""
    res = auditor.audit_systemwide_governance("home_local_services", user_responses=[])
    assert res["scope"] == "SYSTEM_WIDE_ALL_ROLES_AND_SUBSYSTEMS"
    assert "Lead Architect" in res["roles_covered"]
    assert "Systems Engineer" in res["roles_covered"]


def test_six_recommendation_types_allowed(auditor):
    """2. Validates all 6 recommendation types."""
    res = auditor.audit_systemwide_governance("home_local_services", user_responses=[])
    recs = set(res["allowed_recommendations"])
    expected = {"AGREE", "DISAGREE", "REVISE", "STOP", "DEFER", "PROPOSE_ALTERNATIVE"}
    assert recs == expected


def test_anti_churn_rule_enforced(auditor):
    """3. Anti-churn rule explicitly forbids artificial objections/churn."""
    res = auditor.audit_systemwide_governance("home_local_services", user_responses=[])
    assert res["governance_rules"]["is_artificial_churn_forbidden"] is True


def test_non_binding_human_authority_preserved(auditor):
    """4. Preserves non-binding authority of agent recommendations."""
    res = auditor.audit_systemwide_governance("home_local_services", user_responses=[])
    assert res["governance_rules"]["is_human_authority_preserved"] is True


def test_agents_md_updated_with_systemwide_protocol():
    """5. .agents/AGENTS.md contains System-Wide Governance Protocol."""
    content = (REPO_ROOT / ".agents" / "AGENTS.md").read_text(encoding="utf-8")
    assert "System-Wide APE Engineering Judgment & Governance Protocol" in content
    assert "Anti-Churn Rule" in content
    assert "Non-Binding Authority" in content


def test_systems_engineer_md_updated_with_judgment_mandate():
    """6. .agents/roles/systems_engineer.md contains Engineering Judgment responsibility."""
    content = (REPO_ROOT / ".agents" / "roles" / "systems_engineer.md").read_text(encoding="utf-8")
    assert "Engineering Judgment" in content
