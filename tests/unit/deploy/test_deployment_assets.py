"""
Unit tests for Production Deployment Assets (EPIC G8-2).
"""

from pathlib import Path
import pytest


def test_deployment_assets_exist():
    project_root = Path(__file__).parent.parent.parent.parent
    docker_file = project_root / "deploy" / "docker-compose.yml"
    helm_file = project_root / "deploy" / "helm" / "Chart.yaml"

    assert docker_file.exists()
    assert "ape-cloud-server" in docker_file.read_text(encoding="utf-8")

    assert helm_file.exists()
    assert "ape-platform" in helm_file.read_text(encoding="utf-8")
