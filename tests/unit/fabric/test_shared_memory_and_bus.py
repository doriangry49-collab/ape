"""
Unit tests for Shared Memory Workspace and Observation Bus (PR-A4 / PR-A5).
"""

from pathlib import Path

from ape.fabric.bus import FabricEvent, ObservationBus
from ape.fabric.memory import SharedMemoryWorkspace


def test_shared_memory_workspace(tmp_path: Path):
    mem = SharedMemoryWorkspace("calc_app", project_root=tmp_path)
    mem.set("key1", "val1")
    assert mem.get("key1") == "val1"

    mem.add_artifact("art_01", {"file": "main.py"})
    assert mem.get_artifact("art_01") == {"file": "main.py"}

    mem.log_finding("coder", "coder", "Generated main.py")
    assert len(mem.get_all_findings()) == 1


def test_observation_bus_pub_sub():
    bus = ObservationBus()
    received = []

    def handler(evt: FabricEvent):
        received.append(evt)

    bus.subscribe("research_completed", handler)

    evt = FabricEvent(event_type="research_completed", source_agent="researcher", topic_slug="calc_app")
    bus.publish(evt)

    assert len(received) == 1
    assert received[0].source_agent == "researcher"
