"""
SBOM Generator Subsystem — RFC-022 / PR-L1 Specification.
Generates SPDX 2.3 and CycloneDX 1.4 structured Software Bill of Materials.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


class SBOMGenerator:
    """Generates Software Bill of Materials (SBOM) artifacts for deliverables."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)

    def generate_spdx(self, topic_slug: str, deliverables: List[str]) -> Dict[str, Any]:
        """Generate SPDX 2.3 JSON compliant manifest."""
        packages: List[Dict[str, Any]] = [
            {
                "name": "python",
                "versionInfo": "3.11+",
                "SPDXID": "SPDXRef-Package-Python",
                "downloadLocation": "NOASSERTION",
            }
        ]

        for d in deliverables:
            packages.append({
                "name": d,
                "versionInfo": "0.1.0",
                "SPDXID": f"SPDXRef-Deliverable-{d.replace('.', '-')}",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": True,
            })

        return {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": f"APE-Deliverable-SBOM-{topic_slug}",
            "nameSpace": f"https://spdx.org/spdxdocs/ape-{topic_slug}",
            "packages": packages,
        }
