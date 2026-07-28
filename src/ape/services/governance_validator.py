from __future__ import annotations

import json
from pathlib import Path


def validate_project_state(state_file_path: Path) -> dict:
    """Validates project_state.json against the expected schema.
    Raises ValueError if validation fails.
    """
    if not state_file_path.exists():
        raise ValueError(f"State file {state_file_path} does not exist.")
        
    try:
        data = json.loads(state_file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in state file: {e}")
        
    required_keys = [
        "version",
        "current_sprint",
        "last_completed_sprint",
        "repository_status",
        "primary_branch",
        "source_of_truth",
        "current_features",
        "quality_status",
        "constitution",
        "next_goal"
    ]
    
    # Basic field presence checks
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key in state: {key}")
            
    # Value type verification
    if not isinstance(data["version"], str):
        raise ValueError("Field 'version' must be a string.")
        
    if not isinstance(data["current_sprint"], str):
        raise ValueError("Field 'current_sprint' must be a string.")
        
    if not isinstance(data["last_completed_sprint"], str):
        raise ValueError("Field 'last_completed_sprint' must be a string.")
        
    if not isinstance(data["repository_status"], str):
        raise ValueError("Field 'repository_status' must be a string.")
        
    if not isinstance(data["primary_branch"], str):
        raise ValueError("Field 'primary_branch' must be a string.")
        
    if not isinstance(data["source_of_truth"], str):
        raise ValueError("Field 'source_of_truth' must be a string.")
        
    if not isinstance(data["current_features"], list):
        raise ValueError("Field 'current_features' must be a list of strings.")
    for feat in data["current_features"]:
        if not isinstance(feat, str):
            raise ValueError("All items in 'current_features' must be strings.")
            
    if not isinstance(data["constitution"], list):
        raise ValueError("Field 'constitution' must be a list of strings.")
    for const in data["constitution"]:
        if not isinstance(const, str):
            raise ValueError("All items in 'constitution' must be strings.")
            
    if not isinstance(data["next_goal"], str):
        raise ValueError("Field 'next_goal' must be a string.")
        
    # Verify quality_status structure
    qs = data["quality_status"]
    if not isinstance(qs, dict):
        raise ValueError("Field 'quality_status' must be an object.")
        
    for k in ["ruff", "pytest", "test_count"]:
        if k not in qs:
            raise ValueError(f"Missing required key in quality_status: {k}")
            
    if not isinstance(qs["ruff"], str):
        raise ValueError("quality_status.ruff must be a string.")
        
    if not isinstance(qs["pytest"], str):
        raise ValueError("quality_status.pytest must be a string.")
        
    if not isinstance(qs["test_count"], int):
        raise ValueError("quality_status.test_count must be an integer.")
        
    return data
