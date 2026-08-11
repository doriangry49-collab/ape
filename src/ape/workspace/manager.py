"""
Workspace Manager — RFC-022 / PR-W1 Specification.
Implements workspace creation, context switching, listing, and archiving under .workspaces/.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List

from ape.utils import slugify
from ape.workspace.contracts import WorkspaceContext, WorkspaceManifest


class WorkspaceManager:
    """Manager engine for multi-tenant workspace isolation and switching."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.workspaces_dir = self.project_root / ".workspaces"
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.workspaces_dir / "active.json"

    def create_workspace(self, name: str, description: str = "") -> WorkspaceContext:
        """Create a new workspace entry and directory structure."""
        slug = slugify(name)
        ws_dir = self.workspaces_dir / slug
        ws_dir.mkdir(parents=True, exist_ok=True)

        manifest = WorkspaceManifest(name=name, description=description)
        (ws_dir / "manifest.json").write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

        ctx = WorkspaceContext(
            name=name,
            slug=slug,
            root_path=ws_dir,
            active=False,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        (ws_dir / "context.json").write_text(json.dumps(ctx.to_dict(), indent=2), encoding="utf-8")
        return ctx

    def switch_workspace(self, slug_or_name: str) -> WorkspaceContext:
        """Switch current active workspace context."""
        slug = slugify(slug_or_name)
        ws_dir = self.workspaces_dir / slug

        if not ws_dir.exists():
            # Auto-create workspace if not exists
            self.create_workspace(slug_or_name)

        ctx_file = ws_dir / "context.json"
        data = json.loads(ctx_file.read_text(encoding="utf-8")) if ctx_file.exists() else {}

        ctx = WorkspaceContext(
            name=data.get("name", slug_or_name),
            slug=slug,
            root_path=ws_dir,
            active=True,
            created_at=data.get("created_at", "N/A"),
        )
        self.config_file.write_text(json.dumps({"active_slug": slug}, indent=2), encoding="utf-8")
        return ctx

    def get_active_workspace(self) -> WorkspaceContext:
        """Fetch current active workspace or default."""
        active_slug = "default"
        if self.config_file.exists():
            try:
                active_slug = json.loads(self.config_file.read_text(encoding="utf-8")).get("active_slug", "default")
            except Exception:
                pass

        ws_dir = self.workspaces_dir / active_slug
        if not ws_dir.exists():
            return self.create_workspace(active_slug)

        ctx_file = ws_dir / "context.json"
        data = json.loads(ctx_file.read_text(encoding="utf-8")) if ctx_file.exists() else {}

        return WorkspaceContext(
            name=data.get("name", active_slug),
            slug=active_slug,
            root_path=ws_dir,
            active=True,
            created_at=data.get("created_at", "N/A"),
        )

    def list_workspaces(self) -> List[WorkspaceContext]:
        """List all discovered workspace contexts."""
        workspaces: List[WorkspaceContext] = []
        active_slug = self.get_active_workspace().slug

        for child in self.workspaces_dir.iterdir():
            if child.is_dir() and (child / "context.json").exists():
                try:
                    data = json.loads((child / "context.json").read_text(encoding="utf-8"))
                    is_active = (child.name == active_slug)
                    workspaces.append(WorkspaceContext(
                        name=data.get("name", child.name),
                        slug=child.name,
                        root_path=child,
                        active=is_active,
                        created_at=data.get("created_at", "N/A"),
                    ))
                except Exception:
                    pass

        if not workspaces:
            workspaces.append(self.get_active_workspace())

        return workspaces

    def archive_workspace(self, slug_or_name: str) -> bool:
        """Archive a workspace by renaming folder with .archived extension."""
        slug = slugify(slug_or_name)
        ws_dir = self.workspaces_dir / slug
        if ws_dir.exists():
            archived_dir = self.workspaces_dir / f"{slug}.archived"
            ws_dir.rename(archived_dir)
            return True
        return False
