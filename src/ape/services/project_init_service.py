from __future__ import annotations

from pathlib import Path

from ape.project import Project


class ProjectInitializationService:
    """Service dedicated to workspace initialization and creation."""

    def initialize_workspace(
        self,
        current_dir: Path,
        project_root: Path,
    ) -> tuple[Path, Path, Path, bool]:
        project = Project.load(current_dir)
        target_root = project.root
        
        # 1. Create .ape/ and config.toml
        ape_dir = target_root / ".ape"
        ape_dir.mkdir(parents=True, exist_ok=True)
        config_path = ape_dir / "config.toml"
        created = not config_path.exists()
        if created:
            config_path.write_text("[ape]\n", encoding="utf-8")
            
        # 2. Create .governance/ structure
        gov_dir = target_root / ".governance"
        schema_dir = gov_dir / "schema"
        gov_dir.mkdir(parents=True, exist_ok=True)
        schema_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy template files or write defaults
        state_file = gov_dir / "project_state.json"
        if not state_file.exists():
            default_state = {
                "version": "v0.1.0",
                "current_sprint": "Sprint 7.0 – Governance Engine",
                "last_completed_sprint": "Sprint 6.9 – Lightweight Project Factory",
                "repository_status": "Active",
                "primary_branch": "main",
                "source_of_truth": "GitHub",
                "current_features": [
                    "ape doctor",
                    "ape version",
                    "ape init",
                    "ape config",
                    "ape context",
                    "ape validate",
                ],
                "quality_status": {"ruff": "passing", "pytest": "passing", "test_count": 35},
                "constitution": [
                    (
                        "Every module must increase at least one of the following: "
                        "Knowledge, Revenue, Decision Quality. If it increases none "
                        "of them, it does not belong in APE."
                    )
                ],
                "next_goal": "Governance Engine and Self-Governing Repository"
            }
            import json
            state_file.write_text(json.dumps(default_state, indent=2), encoding="utf-8")
            
        yaml_file = gov_dir / "governance.yaml"
        if not yaml_file.exists():
            yaml_content = (
                "version: 1\n"
                "manifesto: 1.1\n"
                "governance: 1.1\n"
                "schema:\n"
                "  state: 1.0\n"
                "  context: 1.0\n"
                "  governance: 1.0\n"
            )
            yaml_file.write_text(yaml_content, encoding="utf-8")

            
        schema_file = schema_dir / "project_state.schema.json"
        if not schema_file.exists():
            default_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "ProjectState",
                "type": "object",
                "properties": {
                    "version": {"type": "string"},
                    "current_sprint": {"type": "string"},
                    "last_completed_sprint": {"type": "string"},
                    "repository_status": {"type": "string"},
                    "primary_branch": {"type": "string"},
                    "source_of_truth": {"type": "string"},
                    "current_features": {"type": "array", "items": {"type": "string"}},
                    "quality_status": {
                        "type": "object",
                        "properties": {
                            "ruff": {"type": "string"},
                            "pytest": {"type": "string"},
                            "test_count": {"type": "integer"}
                        },
                        "required": ["ruff", "pytest", "test_count"]
                    },
                    "constitution": {"type": "array", "items": {"type": "string"}},
                    "next_goal": {"type": "string"}
                },
                "required": [
                    "version", "current_sprint", "last_completed_sprint", "repository_status",
                    "primary_branch", "source_of_truth", "current_features", "quality_status",
                    "constitution", "next_goal"
                ]
            }
            schema_file.write_text(json.dumps(default_schema, indent=2), encoding="utf-8")
            
        return target_root, ape_dir, config_path, created

