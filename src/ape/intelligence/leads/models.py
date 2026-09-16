from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from dataclasses import dataclass, field, asdict


SourceType = Literal["twitter", "github_issue", "forum_post"]
VerificationStatus = Literal["VERIFIED_EXISTS", "UNVERIFIED_OR_404", "ERROR"]


@dataclass
class LeadItem:
    """Represents a single discovered potential lead."""

    source_url: str
    source_type: SourceType
    quote: str
    relevance_reason: str
    suggested_approach: str
    verification_status: VerificationStatus = "UNVERIFIED_OR_404"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "source_type": self.source_type,
            "quote": self.quote,
            "relevance_reason": self.relevance_reason,
            "suggested_approach": self.suggested_approach,
            "verification_status": self.verification_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LeadItem:
        return cls(
            source_url=data["source_url"],
            source_type=data["source_type"],
            quote=data["quote"],
            relevance_reason=data["relevance_reason"],
            suggested_approach=data["suggested_approach"],
            verification_status=data.get("verification_status", "UNVERIFIED_OR_404"),
        )


@dataclass
class LeadReport:
    """Collection of discovered leads for a product and pain point."""

    product: str
    pain_point: str
    discovered_at: str
    total_leads: int
    verified_leads: int
    leads: list[LeadItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "pain_point": self.pain_point,
            "discovered_at": self.discovered_at,
            "total_leads": self.total_leads,
            "verified_leads": self.verified_leads,
            "leads": [lead.to_dict() for lead in self.leads],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LeadReport:
        leads = [LeadItem.from_dict(item) for item in data.get("leads", [])]
        return cls(
            product=data["product"],
            pain_point=data["pain_point"],
            discovered_at=data["discovered_at"],
            total_leads=data["total_leads"],
            verified_leads=data["verified_leads"],
            leads=leads,
        )
