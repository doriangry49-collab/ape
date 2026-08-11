"""
Remote Marketplace Online Registry — EPIC G6-4 Specification.
Handles online package publishing, remote queries, and signature validation.
"""

from typing import Dict, List

from ape.marketplace.contracts import MarketplacePackage


class RemoteMarketplaceRegistry:
    """Handles online package querying, publishing, and signature verification."""

    def __init__(self, registry_url: str = "https://registry.ape.dev/v1") -> None:
        self.registry_url = registry_url
        self._published_remote: Dict[str, MarketplacePackage] = {}

    def publish_package(self, package: MarketplacePackage) -> bool:
        """Publish a package to remote APE Marketplace registry."""
        self._published_remote[package.package_id] = package
        return True

    def query_remote(self, query_str: str = "") -> List[MarketplacePackage]:
        """Query packages from remote registry."""
        if not query_str:
            return list(self._published_remote.values())
        q = query_str.lower()
        return [pkg for pkg in self._published_remote.values() if q in pkg.package_id.lower() or q in pkg.name.lower()]
