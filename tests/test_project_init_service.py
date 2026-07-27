from pathlib import Path

from ape.services.project_init_service import ProjectInitializationService


def test_project_init_service_creates_workspace_and_config(tmp_path) -> None:
    package_root = Path(__file__).resolve().parents[1]
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    service = ProjectInitializationService()

    target_root, ape_dir, config_path, created = service.initialize_workspace(
        current_dir=target_dir,
        project_root=package_root,
    )

    assert target_root == target_dir
    assert ape_dir == target_dir / ".ape"
    assert config_path == target_dir / ".ape" / "config.toml"
    assert created is True
    assert config_path.read_text(encoding="utf-8") == "[ape]\n"


def test_project_init_service_does_not_overwrite_existing_config(tmp_path) -> None:
    package_root = Path(__file__).resolve().parents[1]
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    service = ProjectInitializationService()

    # First init
    service.initialize_workspace(
        current_dir=target_dir,
        project_root=package_root,
    )

    # Modify config to verify it's not overwritten
    config_file = target_dir / ".ape" / "config.toml"
    config_file.write_text("[ape]\nmodified = true\n", encoding="utf-8")

    # Second init
    target_root, ape_dir, config_path, created = service.initialize_workspace(
        current_dir=target_dir,
        project_root=package_root,
    )

    assert created is False
    assert config_file.read_text(encoding="utf-8") == "[ape]\nmodified = true\n"
