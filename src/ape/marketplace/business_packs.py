"""
Business Model Marketplace Packs — ORION-104 Specification.
Sells complete turnkey Business Model Packs rather than simple UI plugins.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BusinessModelPack:
    """Represents a turnkey Business Model Marketplace package."""
    pack_id: str
    pack_name: str
    business_type: str  # saas_startup, youtube_studio, real_estate
    description: str
    included_roles: List[str] = field(default_factory=list)
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize BusinessModelPack into dictionary payload."""
        return {
            "pack_id": self.pack_id,
            "pack_name": self.pack_name,
            "business_type": self.business_type,
            "description": self.description,
            "roles_count": len(self.included_roles),
            "included_roles": self.included_roles,
            "version": self.version,
        }


class BusinessModelPackRegistry:
    """Registry providing turnkey Business Model Packs."""

    def __init__(self) -> None:
        self._packs: Dict[str, BusinessModelPack] = {}
        self._register_default_packs()

    def _register_default_packs(self) -> None:
        # 1. SaaS Startup Pack
        self._packs["pack_saas_startup"] = BusinessModelPack(
            pack_id="pack_saas_startup",
            pack_name="SaaS Startup Pack",
            business_type="saas_startup",
            description="Turnkey SaaS Startup execution team (CEO, CTO, Coder, QA, Marketing, Analytics).",
            included_roles=["CEO", "CTO", "Planner", "Coder", "QA", "DevOps", "Marketing", "Analytics"],
        )

        # 2. YouTube Studio Pack
        self._packs["pack_youtube_studio"] = BusinessModelPack(
            pack_id="pack_youtube_studio",
            pack_name="YouTube Studio Pack",
            business_type="youtube_studio",
            description="Autonomous Media & Channel Production team (Research, Script, Video, SEO, Publishing).",
            included_roles=["Research", "ScriptWriter", "VoiceActor", "VideoEditor", "SEO", "Publisher"],
        )

        # 3. Real Estate Automation Pack
        self._packs["pack_real_estate"] = BusinessModelPack(
            pack_id="pack_real_estate",
            pack_name="Real Estate Automation Pack",
            business_type="real_estate",
            description="Automated Real Estate & Lead Generation team (LeadFinder, CRM, Listing, WhatsApp).",
            included_roles=["LeadFinder", "CRMManager", "WhatsAppBot", "ListingAgent", "Marketing"],
        )

    def list_packs(self) -> List[BusinessModelPack]:
        """Return all available Business Model Packs."""
        return list(self._packs.values())

    def get_pack(self, pack_id: str) -> Optional[BusinessModelPack]:
        """Fetch Business Model Pack by ID."""
        return self._packs.get(pack_id)
