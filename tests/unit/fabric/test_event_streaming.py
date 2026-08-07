"""
Unit tests for EventStreamEngine (EPIC G6-3).
"""

import time
import pytest

from ape.fabric.streaming import EventStreamEngine, StreamEvent


def test_event_stream_pub_sub():
    engine = EventStreamEngine()
    received = []

    def on_event(evt: StreamEvent):
        received.append(evt)

    engine.subscribe("pipeline.events", on_event)

    event = StreamEvent(
        topic="pipeline.events",
        event_type="BUILD_COMPLETED",
        payload={"topic_slug": "calc_app", "passed": True},
        timestamp=time.time(),
    )
    count = engine.publish(event)

    assert count == 1
    assert len(received) == 1
    assert received[0].event_type == "BUILD_COMPLETED"
