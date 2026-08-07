"""
ArtifactAssembler Layer — ORION-106B Specification.
Single dedicated layer responsible for materializing ArtifactBundle objects to target destinations (Local Disk, ZIP Archive, GitHub).
"""

from pathlib import Path

from ape.business.artifacts import ArtifactBundle


class ArtifactAssembler:
    """Enterprise assembly engine materializing ArtifactBundle domain objects to physical targets."""

    @staticmethod
    def assemble_to_disk(bundle: ArtifactBundle, target_dir: Path) -> list[Path]:
        """
        Materialize ArtifactBundle files cleanly to target directory on disk.
        Creates parent directories as required.
        """
        target_dir = Path(target_dir)
        written_files: list[Path] = []

        for artifact in bundle.files:
            file_path = target_dir / artifact.relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(artifact.content, encoding="utf-8")
            written_files.append(file_path)

        return written_files

    @staticmethod
    def assemble_to_zip(bundle: ArtifactBundle, zip_path: Path) -> Path:
        """Compress ArtifactBundle files into a deployment ZIP archive."""
        import zipfile
        zip_path = Path(zip_path)
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for artifact in bundle.files:
                zf.writestr(artifact.relative_path, artifact.content)

        return zip_path
