"""
Quality OS Cryptographic Evidence Binder — RFC-022 Specification.
Computes SHA-256 hashes for all physical quality reports and logs, building a Merkle tree digest (`quality_merkle_root`)
bound to governance evidence streams.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict


class QualityEvidenceBinder:
    """Computes SHA-256 digests and Merkle root hashes for physical Quality OS artifacts."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.reports_dir = self.project_root / ".build" / "quality" / "reports"
        self.logs_dir = self.project_root / ".build" / "quality" / "logs"

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a single file."""
        if not file_path.exists() or not file_path.is_file():
            return ""
        hasher = hashlib.sha256()
        hasher.update(file_path.read_bytes())
        return hasher.hexdigest()

    def build_evidence_manifest(self) -> Dict[str, Any]:
        """
        Scans `.build/quality/reports/` and `.build/quality/logs/`.
        Calculates SHA-256 hashes for all physical artifacts and computes the Merkle root digest.
        """
        artifact_hashes: Dict[str, str] = {}

        # Scan reports
        if self.reports_dir.exists():
            for p in sorted(self.reports_dir.glob("*")):
                if p.is_file():
                    artifact_hashes[f"reports/{p.name}"] = self.calculate_file_hash(p)

        # Scan logs
        if self.logs_dir.exists():
            for p in sorted(self.logs_dir.glob("*")):
                if p.is_file():
                    artifact_hashes[f"logs/{p.name}"] = self.calculate_file_hash(p)

        # Compute Merkle Root Digest
        merkle_hasher = hashlib.sha256()
        for rel_name in sorted(artifact_hashes.keys()):
            h = artifact_hashes[rel_name]
            merkle_hasher.update(f"{rel_name}:{h}".encode("utf-8"))

        merkle_root = merkle_hasher.hexdigest() if artifact_hashes else "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        return {
            "quality_merkle_root": merkle_root,
            "artifact_count": len(artifact_hashes),
            "artifact_hashes": artifact_hashes,
        }
