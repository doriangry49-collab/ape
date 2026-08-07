"""
Unit tests for TopicDAGEngine (PR-W3 / PR-W4).
"""

import pytest

from ape.workspace.dag import TopicDAGEngine


def test_topic_dag_engine_execution():
    dag = TopicDAGEngine()

    dag.add_topic_stage("app", "research")
    dag.add_topic_stage("app", "architecture", dependencies=["app:research"])
    dag.add_topic_stage("app", "implementation", dependencies=["app:architecture"])
    dag.add_topic_stage("app", "qa", dependencies=["app:implementation"])
    dag.add_topic_stage("app", "release", dependencies=["app:qa"])

    order = dag.get_execution_order()
    stages = [node.stage_name for node in order]
    assert stages == ["research", "architecture", "implementation", "qa", "release"]

    res = dag.execute_dag()
    assert res["nodes_executed"] == 5
    assert res["results"]["app:release"] == "COMPLETED"
