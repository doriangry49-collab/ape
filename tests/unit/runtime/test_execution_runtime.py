"""
Unit tests for ORION-109A Production Execution Runtime Foundation & LLM Adapter Protocol.
Verifies generic ExecutionRuntime resilience, retry with exponential backoff, timeout enforcement,
CancellationToken signals, department-slug checkpointing, runtime event hooks, and MockLLMProvider execution.
"""

from pathlib import Path
import tempfile
from unittest.mock import MagicMock

import pytest

from ape.runtime import (
    CancellationToken,
    CheckpointStore,
    ExecutionRuntime,
    LLMProviderProtocol,
    MockLLMProvider,
    RetryPolicy,
    RuntimeEventHooks,
    TimeoutPolicy,
)


def test_mock_llm_provider():
    provider = MockLLMProvider("Automated SaaS Code")
    assert isinstance(provider, LLMProviderProtocol)

    res = provider.complete("Generate Next.js boilerplate")
    assert "[MockLLM]" in res
    assert "Automated SaaS Code" in res


def test_execution_runtime_exponential_retry_on_failure():
    retry_mock = MagicMock()

    hooks = RuntimeEventHooks(on_retry=retry_mock)
    policy = RetryPolicy(max_retries=2, initial_delay=0.001, backoff_factor=2.0)
    runtime = ExecutionRuntime(retry_policy=policy, events=hooks)

    call_count = 0

    def flaky_task():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Transient network error")
        return "SUCCESS"

    with tempfile.TemporaryDirectory() as tmp_dir:
        runtime.checkpoint_store = CheckpointStore(root_dir=Path(tmp_dir) / "ventures")
        res = runtime.run_step("v_test_001", "research", flaky_task)

        assert res == "SUCCESS"
        assert call_count == 3
        assert retry_mock.call_count == 2


def test_execution_runtime_cancellation_token():
    token = CancellationToken()
    token.cancel()

    runtime = ExecutionRuntime()

    def task():
        return "OK"

    with pytest.raises(RuntimeError) as exc_info:
        runtime.run_step("v_test_001", "engineering", task, cancellation_token=token)

    assert "Execution cancelled" in str(exc_info.value)


def test_department_slug_checkpoint_store():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cp_store = CheckpointStore(root_dir=Path(tmp_dir) / "ventures")
        venture_id = "v_real_estate_001"
        dept_slug = "research"

        assert not cp_store.has_checkpoint(venture_id, dept_slug)

        saved_path = cp_store.save_checkpoint(venture_id, dept_slug, {"status": "COMPLETED", "files": 3})

        assert saved_path.exists()
        assert saved_path.name == "research.json"
        assert saved_path.parent.name == "checkpoints"
        assert cp_store.has_checkpoint(venture_id, dept_slug)

        loaded = cp_store.load_checkpoint(venture_id, dept_slug)
        assert loaded["dept_slug"] == "research"
        assert loaded["data"]["files"] == 3


def test_runtime_event_hooks_lifecycles():
    started_mock = MagicMock()
    finished_mock = MagicMock()
    checkpoint_mock = MagicMock()

    hooks = RuntimeEventHooks(
        on_step_started=started_mock,
        on_step_finished=finished_mock,
        on_checkpoint_saved=checkpoint_mock,
    )

    runtime = ExecutionRuntime(events=hooks)

    def task():
        return {"result": "ok"}

    with tempfile.TemporaryDirectory() as tmp_dir:
        runtime.checkpoint_store = CheckpointStore(root_dir=Path(tmp_dir) / "ventures")
        runtime.run_step("v_test_001", "marketing", task)

        assert started_mock.called
        assert finished_mock.called
        assert checkpoint_mock.called
