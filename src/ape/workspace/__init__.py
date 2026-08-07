"""
APE Workspace Operating System Subsystem — RFC-022 / PR-W1 to PR-W6 Specification.
"""

from pathlib import Path

from ape.workspace.contracts import WorkspaceContext, WorkspaceManifest
from ape.workspace.dag import TopicDAGEngine, TopicNode
from ape.workspace.knowledge_graph import EnterpriseKnowledgeGraph, KnowledgeNode
from ape.workspace.manager import WorkspaceManager
from ape.workspace.project import ProjectNode, ProjectTopology


def find_workspace_dir(start_dir: Path | None = None) -> Path | None:
    """Discover an APE workspace by searching upward for .ape/config.toml."""
    current_dir = (start_dir or Path.cwd()).resolve()

    for directory in [current_dir, *current_dir.parents]:
        config_path = directory / ".ape" / "config.toml"
        if config_path.exists():
            return directory

    return None


__all__ = [
    "find_workspace_dir",
    "WorkspaceContext",
    "WorkspaceManifest",
    "WorkspaceManager",
    "ProjectNode",
    "ProjectTopology",
    "TopicNode",
    "TopicDAGEngine",
    "KnowledgeNode",
    "EnterpriseKnowledgeGraph",
]
