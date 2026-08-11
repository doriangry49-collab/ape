"""
Package Installer Engine — RFC-107 / EPIC-11A Specification.
Installs and registers official/community plugins, agents, and business units.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from ape.marketplace.contracts import MarketplacePackage
from ape.marketplace.index import MarketplaceIndex


class PackageInstaller:
    """Handles package installation, verification, and local manifest registration."""

    def __init__(self, project_root: Path, index: Optional[MarketplaceIndex] = None) -> None:
        self.project_root = Path(project_root)
        self.index = index or MarketplaceIndex()
        self.installed_dir = self.project_root / ".marketplace" / "installed"
        self.installed_dir.mkdir(parents=True, exist_ok=True)

    def install_package(self, package_id: str) -> MarketplacePackage:
        """Install package by ID after signature verification."""
        pkg = self.index.get_package(package_id)
        if not pkg:
            raise ValueError(f"Package '{package_id}' not found in Marketplace index.")

        if not self.index.verify_signature(pkg):
            raise ValueError(f"Signature verification failed for package '{package_id}'.")

        pkg_file = self.installed_dir / f"{pkg.package_id}.json"
        pkg_file.write_text(json.dumps(pkg.to_dict(), indent=2), encoding="utf-8")
        return pkg

    def list_installed(self) -> List[MarketplacePackage]:
        """List all locally installed marketplace packages."""
        installed: List[MarketplacePackage] = []
        for child in self.installed_dir.glob("*.json"):
            try:
                data = json.loads(child.read_text(encoding="utf-8"))
                installed.append(MarketplacePackage(
                    package_id=data["package_id"],
                    name=data["name"],
                    version=data["version"],
                    package_type=data["package_type"],
                    description=data.get("description", ""),
                    author=data.get("author", ""),
                    signature_sha256=data.get("signature_sha256", ""),
                    verified=data.get("verified", True),
                ))
            except Exception:
                pass
        return installed
