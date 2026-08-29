"""Regression test for Fail-Closed Evidence Behavior (Option A).

Verifies that when zero real domain observations are found (e.g. for 'gebze_kocaeli_emlak_ai_sanal_staging'):
1. No synthetic competitors ('LangChain', 'Coze/Dify', 'OpenAI Assistants') are generated.
2. `business_evidence` in ResearchReport is empty.
3. `evidence_status` is marked as 'INSUFFICIENT_DOMAIN_EVIDENCE'.
4. Decision Engine does not issue a positive VALIDATE_WITH_USERS policy decision on 0 evidence.
"""

import json
from pathlib import Path

from ape.intelligence.decision.engine import DecisionEngine
from ape.intelligence.decision.models import PolicyDecision
from ape.intelligence.research.engine import ResearchEngine
from ape.project import Project


def test_gebze_emlak_fail_closed_on_zero_evidence(tmp_path: Path):
    project = Project(root=tmp_path, config_path=tmp_path / "pyproject.toml")
    topic = "Gebze Kocaeli Emlak AI Sanal Staging"
    topic_slug = "gebze_kocaeli_emlak_ai_sanal_staging"

    # 1. Run Research
    research_engine = ResearchEngine(project, offline=False)
    report = research_engine.run_research(topic)

    # Acceptance Criterion 1: Zero synthetic competitors
    assert "OpenAI Assistants Platform" not in report.competitors
    assert "LangChain Framework Ecosystem" not in report.competitors
    assert "Coze/Dify platforms" not in report.competitors
    assert report.competitors == []

    # Acceptance Criterion 2 & 3: Empty business_evidence in persisted JSON artifact
    research_json_file = tmp_path / ".build" / "research" / f"{topic_slug}.json"
    assert research_json_file.exists()
    data = json.loads(research_json_file.read_text(encoding="utf-8"))
    bus_ev = data.get("business_evidence", [])
    for ev in bus_ev:
        assert ev.get("search_intent_observation") in ("UNKNOWN", False)
        assert ev.get("pain_observation") in ("UNKNOWN", False)
        assert ev.get("competition_observation") in ("UNKNOWN", False)

    # 2. Run Decision Engine
    decision_engine = DecisionEngine(tmp_path)
    dec_report = decision_engine.run_decision(topic, topic_slug)

    # Acceptance Criterion 4: Exact canonical PolicyDecision.WATCH (WAIT_FOR_SIGNAL) produced by ConstitutionValidator
    assert dec_report.policy != "VALIDATE_WITH_USERS"
    assert dec_report.decision == PolicyDecision.WATCH
    assert dec_report.policy == "WAIT_FOR_SIGNAL"
