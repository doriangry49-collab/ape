"""
Unit tests for Marketplace Core and Package Installer (EPIC-11A).
"""

from pathlib import Path

from ape.marketplace import MarketplaceIndex, PackageInstaller


def test_marketplace_index_queries():
    index = MarketplaceIndex()
    plugins = index.query_packages(package_type="plugin")
    agents = index.query_packages(package_type="agent")

    assert len(plugins) >= 2
    assert len(agents) >= 1
    assert any(p.package_id == "ape-plugin-python" for p in plugins)


def test_marketplace_package_installer(tmp_path: Path):
    installer = PackageInstaller(tmp_path)
    pkg = installer.install_package("ape-plugin-python")

    assert pkg.package_id == "ape-plugin-python"
    installed = installer.list_installed()
    assert len(installed) == 1
    assert installed[0].package_id == "ape-plugin-python"
