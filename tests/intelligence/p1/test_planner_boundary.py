import json

import pytest

from ape.intelligence.roadmap.engine import RoadmapGenerator
from ape.intelligence.roadmap.llm import PlannerModel


class MockPlannerModel(PlannerModel):
    def __init__(self, response_dict: dict, should_fail: bool = False):
        self.response_dict = response_dict
        self.should_fail = should_fail
        
    def generate(self, prompt: str, system_message: str, schema: dict) -> dict:
        if self.should_fail:
            raise RuntimeError("Mock API Failure")
        return self.response_dict

@pytest.fixture
def setup_project(tmp_path):
    project_root = tmp_path / "ape_project"
    project_root.mkdir()
    
    # Create fake decision artifact
    decisions_dir = project_root / ".build" / "decisions"
    decisions_dir.mkdir(parents=True)
    decision_file = decisions_dir / "test_topic.json"
    decision_data = {
        "decision_id": "dec_mock_01",
        "decision": "BUILD",
        "policy": "Core BUILD Policy",
        "evidence_hash": "hash123",
        "evidence": {"ai_solvability": True}
    }
    decision_file.write_text(json.dumps(decision_data))
    
    # Create config file with API key to trigger planner
    config_dir = project_root / ".ape"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        '[ape.planner]\n'
        'provider = "openai"\n'
        'model = "gpt-4o"\n'
        'api_key = "sk-mock-key"\n'
    )
    
    return project_root

def test_planner_happy_path(setup_project, monkeypatch):
    from ape.intelligence.roadmap.engine import RoadmapGenerator
    
    valid_response = {
        "decision_id": "dec_mock_01",
        "policy_decision": "BUILD",
        "reasoning": "Looks good",
        "milestones": [
            {
                "milestone_id": "m1",
                "title": "Test Milestone",
                "dependencies": [],
                "tasks": [
                    {
                        "task_id": "t1",
                        "description": "Do stuff",
                        "action": "create_file",
                        "deliverables": ["code.py"],
                        "estimated_effort": "1 day"
                    }
                ]
            }
        ]
    }
    
    # Mock the LLM provider instantiation inside RoadmapGenerator
    def mock_init(*args, **kwargs):
        return MockPlannerModel(valid_response)
        
    monkeypatch.setattr("ape.intelligence.roadmap.engine.OpenAICompatibleProvider", mock_init)
    
    generator = RoadmapGenerator(setup_project)
    roadmap = generator.generate_roadmap("test_topic", "test_topic")
    
    assert roadmap.metadata["generator"] == "intelligent-planner"
    assert len(roadmap.milestones) == 1
    assert roadmap.milestones[0].tasks[0].action == "create_file"
    assert roadmap.decision_id == "dec_mock_01"

def test_planner_policy_mutation_rejected(setup_project, monkeypatch):
    # Planner tries to change BUILD to VALIDATE
    mutated_response = {
        "decision_id": "dec_mock_01",
        "policy_decision": "VALIDATE",
        "reasoning": "I think we should validate instead",
        "milestones": []
    }
    
    def mock_init(*args, **kwargs):
        return MockPlannerModel(mutated_response)
        
    monkeypatch.setattr("ape.intelligence.roadmap.engine.OpenAICompatibleProvider", mock_init)
    
    generator = RoadmapGenerator(setup_project)
    roadmap = generator.generate_roadmap("test_topic", "test_topic")
    
    # Should catch ValueError and fallback
    assert roadmap.metadata["generator"] == "heuristic-template"

def test_planner_lineage_mismatch_rejected(setup_project, monkeypatch):
    # Planner returns wrong decision_id
    mutated_response = {
        "decision_id": "forged_decision_id",
        "policy_decision": "BUILD",
        "reasoning": "Forged",
        "milestones": []
    }
    
    def mock_init(*args, **kwargs):
        return MockPlannerModel(mutated_response)
        
    monkeypatch.setattr("ape.intelligence.roadmap.engine.OpenAICompatibleProvider", mock_init)
    
    generator = RoadmapGenerator(setup_project)
    roadmap = generator.generate_roadmap("test_topic", "test_topic")
    
    # Should fallback
    assert roadmap.metadata["generator"] == "heuristic-template"

@pytest.mark.parametrize("action", [
    "run_bash_script",
    "system_call",
    "eval",
    "arbitrary_unknown_action",
    "shell_command",
    "exec",
])
def test_planner_adversarial_actions_rejected(setup_project, monkeypatch, action):
    malicious_response = {
        "decision_id": "dec_mock_01",
        "policy_decision": "BUILD",
        "reasoning": "Adversarial proposal",
        "milestones": [
            {
                "milestone_id": "m1",
                "title": "Test Milestone",
                "dependencies": [],
                "tasks": [
                    {
                        "task_id": "t1",
                        "description": "Exploit",
                        "action": action,
                        "deliverables": [],
                        "estimated_effort": "1 day"
                    }
                ]
            }
        ]
    }
    
    def mock_init(*args, **kwargs):
        return MockPlannerModel(malicious_response)
        
    monkeypatch.setattr("ape.intelligence.roadmap.engine.OpenAICompatibleProvider", mock_init)
    
    generator = RoadmapGenerator(setup_project)
    roadmap = generator.generate_roadmap("test_topic", "test_topic")
    
    # Must fallback to deterministic template when unknown/adversarial action is proposed
    assert roadmap.metadata["generator"] == "heuristic-template"


@pytest.mark.parametrize("action", [
    "create_file", "modify_file", "delete_file", "read_file",
    "run_tests", "git_diff", "git_commit", "git_push",
    "deploy", "external_api_write", "search", "analyze"
])
def test_planner_canonical_actions_accepted(setup_project, monkeypatch, action):
    valid_response = {
        "decision_id": "dec_mock_01",
        "policy_decision": "BUILD",
        "reasoning": "Valid canonical task proposal",
        "milestones": [
            {
                "milestone_id": "m1",
                "title": "Test Milestone",
                "dependencies": [],
                "tasks": [
                    {
                        "task_id": "t1",
                        "description": "Legitimate step",
                        "action": action,
                        "deliverables": ["output.txt"],
                        "estimated_effort": "1 day"
                    }
                ]
            }
        ]
    }
    
    def mock_init(*args, **kwargs):
        return MockPlannerModel(valid_response)
        
    monkeypatch.setattr("ape.intelligence.roadmap.engine.OpenAICompatibleProvider", mock_init)
    
    generator = RoadmapGenerator(setup_project)
    roadmap = generator.generate_roadmap("test_topic", "test_topic")
    
    # Must accept canonical actions at the proposal level
    assert roadmap.metadata["generator"] == "intelligent-planner"
    assert roadmap.milestones[0].tasks[0].action == action


def test_planner_fallback_on_api_error(setup_project, monkeypatch):
    def mock_init(*args, **kwargs):
        return MockPlannerModel({}, should_fail=True)
        
    monkeypatch.setattr("ape.intelligence.roadmap.engine.OpenAICompatibleProvider", mock_init)
    
    generator = RoadmapGenerator(setup_project)
    roadmap = generator.generate_roadmap("test_topic", "test_topic")
    
    # Should fallback
    assert roadmap.metadata["generator"] == "heuristic-template"
