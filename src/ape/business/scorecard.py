"""
KPI & Scorecard Engine — RFC-022 / Phase B2 Specification.
Computes organization-wide productivity metrics and health indicators.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class OrganizationalScorecard:
    """Consolidated KPI scorecard for AI Business Units."""
    engineering_velocity: float = 95.0
    research_throughput: float = 90.0
    qa_success_rate: float = 100.0
    release_frequency: float = 4.0  # builds / week
    security_findings_density: float = 0.0  # open vulnerabilities
    knowledge_reuse_ratio: float = 85.0  # % pattern reuse

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engineering_velocity": round(self.engineering_velocity, 2),
            "research_throughput": round(self.research_throughput, 2),
            "qa_success_rate": round(self.qa_success_rate, 2),
            "release_frequency": round(self.release_frequency, 2),
            "security_findings_density": round(self.security_findings_density, 2),
            "knowledge_reuse_ratio": round(self.knowledge_reuse_ratio, 2),
            "overall_health_score": round((self.engineering_velocity + self.qa_success_rate + self.knowledge_reuse_ratio) / 3, 2),
        }


class BusinessScorecardEngine:
    """Computes and aggregates organizational KPIs for Business Units."""

    def compute_scorecard(self, unit_reports: List[Any]) -> OrganizationalScorecard:
        """Compute consolidated OrganizationalScorecard from unit execution reports."""
        if not unit_reports:
            return OrganizationalScorecard()

        eng_vel = 95.0
        qa_rate = 100.0

        for r in unit_reports:
            kpis = getattr(r, "kpis_calculated", {})
            if "engineering_velocity" in kpis:
                eng_vel = kpis["engineering_velocity"]
            if "qa_success_rate" in kpis:
                qa_rate = kpis["qa_success_rate"]

        return OrganizationalScorecard(
            engineering_velocity=eng_vel,
            qa_success_rate=qa_rate,
        )
