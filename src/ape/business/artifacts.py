"""
Typed Artifact Bundle Schemas — ORION-106B Specification.
Decouples Business Unit logic from raw File I/O by defining strongly typed ArtifactBundle domain objects.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ArtifactFile:
    """Represents a single file payload inside an ArtifactBundle."""
    relative_path: str
    content: str
    is_binary: bool = False


@dataclass
class ArtifactBundle:
    """Base domain object for typed artifact bundles produced by Business Units."""
    bundle_id: str
    bundle_type: str  # research, build, marketing, deployment
    unit_slug: str
    files: List[ArtifactFile] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ArtifactBundle metadata."""
        return {
            "bundle_id": self.bundle_id,
            "bundle_type": self.bundle_type,
            "unit_slug": self.unit_slug,
            "files_count": len(self.files),
            "paths": [f.relative_path for f in self.files],
            "created_at": self.created_at,
        }


class ResearchArtifactBundle(ArtifactBundle):
    """Specialized bundle for Research Department outputs."""

    @classmethod
    def create(cls, topic: str, competitors: List[str], pain_points: List[str]) -> "ResearchArtifactBundle":
        bid = f"bundle_res_{hashlib.sha256(f'{topic}:{time.time()}'.encode()).hexdigest()[:8]}"
        files = [
            ArtifactFile(
                relative_path="research/competitor_analysis.md",
                content=f"# Competitor Analysis for {topic}\n\nKey Competitors:\n" + "\n".join([f"- {c}" for c in competitors]),
            ),
            ArtifactFile(
                relative_path="research/pain_points.json",
                content=json.dumps({"topic": topic, "pain_points": pain_points}, indent=2),
            ),
            ArtifactFile(
                relative_path="research/market_size.md",
                content=f"# Market Size & Opportunity Report for {topic}\n\nEstimated TAM: $500M+ ARR.",
            ),
        ]
        return cls(bundle_id=bid, bundle_type="research", unit_slug="research", files=files)


class BuildArtifactBundle(ArtifactBundle):
    """Specialized bundle for Engineering Department build outputs."""

    @classmethod
    def create(cls, product_name: str) -> "BuildArtifactBundle":
        bid = f"bundle_build_{hashlib.sha256(f'{product_name}:{time.time()}'.encode()).hexdigest()[:8]}"
        files = [
            ArtifactFile(
                relative_path="repo/src/main.py",
                content=f'"""Main entry point for {product_name}."""\n\ndef main():\n    print("Running {product_name} v1.0")\n\nif __name__ == "__main__":\n    main()\n',
            ),
            ArtifactFile(
                relative_path="repo/tests/test_app.py",
                content='def test_app():\n    assert True\n',
            ),
            ArtifactFile(
                relative_path="repo/Dockerfile",
                content='FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nCMD ["python", "repo/src/main.py"]\n',
            ),
            ArtifactFile(
                relative_path="repo/README.md",
                content=f'# {product_name}\n\nGenerated autonomously by APE v1.0 Engineering Unit.\n',
            ),
        ]
        return cls(bundle_id=bid, bundle_type="build", unit_slug="engineering", files=files)


class MarketingArtifactBundle(ArtifactBundle):
    """Specialized bundle for Marketing Department campaign outputs."""

    @classmethod
    def create(cls, product_name: str, landing_html: str) -> "MarketingArtifactBundle":
        bid = f"bundle_mkt_{hashlib.sha256(f'{product_name}:{time.time()}'.encode()).hexdigest()[:8]}"
        files = [
            ArtifactFile(relative_path="marketing/landing_page.html", content=landing_html),
            ArtifactFile(
                relative_path="marketing/sales_copy.md",
                content=f"# Sales Copywriting for {product_name}\n\nAutomate your workflows in 5 minutes.",
            ),
            ArtifactFile(
                relative_path="marketing/seo_metadata.json",
                content=json.dumps({"title": product_name, "keywords": ["automation", "saas", "ai"]}, indent=2),
            ),
        ]
        return cls(bundle_id=bid, bundle_type="marketing", unit_slug="marketing", files=files)


class DeploymentArtifactBundle(ArtifactBundle):
    """Specialized bundle for Publishing Department deployment outputs."""

    @classmethod
    def create(cls, product_name: str, deploy_url: str) -> "DeploymentArtifactBundle":
        bid = f"bundle_pub_{hashlib.sha256(f'{product_name}:{time.time()}'.encode()).hexdigest()[:8]}"
        files = [
            ArtifactFile(
                relative_path="publishing/deployment_manifest.json",
                content=json.dumps({"product_name": product_name, "deploy_url": deploy_url, "status": "LIVE"}, indent=2),
            ),
        ]
        return cls(bundle_id=bid, bundle_type="deployment", unit_slug="publishing", files=files)
