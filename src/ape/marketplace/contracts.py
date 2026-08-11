"""
Marketplace Core Contracts — RFC-107 / EPIC-11A Specification.
Defines MarketplacePackage and PackageManifest schemas for plugins, agents, and business units.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class MarketplacePackage:
    """Represents a registered package in APE Marketplace."""
    package_id: str
    name: str
    version: str
    package_type: str  # plugin, agent, business_unit
    description: str = ""
    author: str = ""
    signature_sha256: str = ""
    verified: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "name": self.name,
            "version": self.version,
            "package_type": self.package_type,
            "description": self.description,
            "author": self.author,
            "signature_sha256": self.signature_sha256,
            "verified": self.verified,
            "metadata": self.metadata,
        }
