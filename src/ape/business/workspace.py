"""
Venture WorkspaceManager — ORION-107 Specification.
Provides multi-venture workspace directory isolation (.build/ventures/{venture_id}/)
and packages consolidated release archives.
"""

from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional
import zipfile

from ape.business.artifacts import ArtifactBundle
from ape.business.assembler import ArtifactAssembler


class VentureWorkspaceManager:
    """Manages isolated directory trees and release packaging for multi-venture execution."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root_dir = Path(root_dir) if root_dir else Path(".build/ventures")
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, venture_id: str) -> Path:
        """Provision an isolated workspace directory for a venture."""
        workspace = self.root_dir / venture_id
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def get_workspace_path(self, venture_id: str) -> Path:
        """Return the root path of a venture workspace."""
        return self.root_dir / venture_id

    def save_bundle(self, venture_id: str, bundle: ArtifactBundle) -> List[Path]:
        """Materialize an ArtifactBundle into the venture's isolated workspace."""
        workspace = self.create_workspace(venture_id)
        return ArtifactAssembler.assemble_to_disk(bundle, workspace)

    def list_ventures(self) -> List[str]:
        """Enumerate active venture workspace directory names."""
        if not self.root_dir.exists():
            return []
        return [d.name for d in self.root_dir.iterdir() if d.is_dir()]

    def package_venture_release(self, venture_id: str, output_zip: Optional[Path] = None) -> Path:
        """
        Consolidate all department artifacts in a venture workspace into a release ZIP archive.
        Returns the path to the written ZIP archive.
        """
        workspace = self.get_workspace_path(venture_id)
        if not workspace.exists():
            raise FileNotFoundError(f"Venture workspace '{venture_id}' does not exist.")

        if output_zip is None:
            releases_dir = self.root_dir.parent / "releases"
            releases_dir.mkdir(parents=True, exist_ok=True)
            output_zip = releases_dir / f"{venture_id}_release.zip"
        else:
            output_zip = Path(output_zip)
            output_zip.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in workspace.rglob("*"):
                if file_path.is_file():
                    relative_in_zip = file_path.relative_to(workspace)
                    zf.write(file_path, str(relative_in_zip))

        return output_zip
