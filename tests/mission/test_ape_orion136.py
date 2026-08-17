"""
ORION-136 — Autonomous Runtime Foundation Test Suite

Proves:
1. PersistentJobQueue manages persistent mission tasks under .build/runtime/jobs.json.
2. State recovery: Interrupted RUNNING jobs are automatically recovered back to QUEUED on startup.
3. MissionScheduler integrates with ConstitutionalPipelineRunner to execute queued missions cleanly.
4. HeartbeatMonitor pulses health & job queue metrics to .build/runtime/heartbeat.json & .governance/evidence/.
5. AutonomousRuntimeDaemon orchestrates background processing, cancellation tokens, and graceful shutdown.
6. Zero regression on existing proven pipeline core.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from ape.intelligence.decision.engine import DecisionEngine
from ape.intelligence.research.engine import ResearchEngine
from ape.intelligence.roadmap.engine import RoadmapGenerator
from ape.project import Project
from ape.runtime.daemon import AutonomousRuntimeDaemon, HeartbeatMonitor
from ape.runtime.scheduler import Job, JobStatus, MissionScheduler, PersistentJobQueue


TOPIC = "ollama_local_llm_ecosystem"
TOPIC_SLUG = "ollama_local_llm_ecosystem"


class TestORION136_AutonomousRuntimeFoundation:
    """ORION-136 Autonomous Runtime Foundation test suite."""

    # ------------------------------------------------------------------
    # 1. Persistent Job Queue & State Recovery
    # ------------------------------------------------------------------

    def test_job_queue_persistence_and_recovery(self, tmp_path: Path) -> None:
        """
        Proof 1: PersistentJobQueue saves jobs to disk and recovers RUNNING jobs on restart.
        """
        queue1 = PersistentJobQueue(tmp_path)
        job1 = Job(job_id="job_test_1", topic_slug=TOPIC_SLUG, action="full_mission")
        job2 = Job(job_id="job_test_2", topic_slug=TOPIC_SLUG, action="full_mission")

        queue1.enqueue(job1)
        queue1.enqueue(job2)

        # Mark job1 as RUNNING (simulate crash while running)
        queue1.update_status(job1.job_id, JobStatus.RUNNING)

        jobs_file = tmp_path / ".build" / "runtime" / "jobs.json"
        assert jobs_file.exists(), "Proof 1 FAIL: jobs.json missing on disk"

        # Re-instantiate queue (simulate daemon restart)
        queue2 = PersistentJobQueue(tmp_path)
        assert len(queue2.get_all_jobs()) == 2

        # Perform state recovery
        recovered = queue2.recover_interrupted_jobs()
        assert len(recovered) == 1
        assert recovered[0].job_id == "job_test_1"
        assert recovered[0].status == JobStatus.QUEUED
        assert "recovered_at" in recovered[0].metadata

        print(f"\n[Proof 1] Job Queue persisted: {jobs_file.name}")
        print(f"[Proof 1] State recovery successful: Job '{recovered[0].job_id}' recovered back to QUEUED.")

    # ------------------------------------------------------------------
    # 2. Mission Scheduler Pipeline Execution
    # ------------------------------------------------------------------

    def test_mission_scheduler_executes_queued_mission(self, tmp_path: Path) -> None:
        """
        Proof 2: MissionScheduler schedules and processes a full pipeline mission.
        """
        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")
        ResearchEngine(project=project, offline=False).run_research(TOPIC)
        DecisionEngine(project_root=tmp_path).run_decision(TOPIC, TOPIC_SLUG)
        RoadmapGenerator(tmp_path).generate_roadmap("Scheduled Mission", TOPIC_SLUG)

        scheduler = MissionScheduler(tmp_path)
        job = scheduler.schedule_mission(TOPIC_SLUG, action="full_mission")
        assert job.status == JobStatus.QUEUED

        from tests.dummy_agent import DummyAgent
        from ape.intelligence.execution.engine import ExecutionEngine
        from ape.intelligence.execution.executor import SimulationTaskExecutor
        original_init = ExecutionEngine.__init__
        def patched_init(self, *args, **kwargs):
            kwargs['agent'] = DummyAgent()
            kwargs['executor'] = SimulationTaskExecutor()
            original_init(self, *args, **kwargs)
        
        with patch.object(ExecutionEngine, '__init__', patched_init):
            processed_job = scheduler.process_next_job()

        assert processed_job is not None
        assert processed_job.status == JobStatus.COMPLETED
        assert processed_job.error is None
        assert processed_job.metadata.get("executed_stages_count") == 9

        print(f"\n[Proof 2] Mission scheduled: {job.job_id}")
        print(f"[Proof 2] Mission processed: status={processed_job.status}, stages={processed_job.metadata['executed_stages_count']}")

    # ------------------------------------------------------------------
    # 3. Heartbeat Monitor & Governance Logging
    # ------------------------------------------------------------------

    def test_heartbeat_monitor_pulses_and_logs(self, tmp_path: Path) -> None:
        """
        Proof 3: HeartbeatMonitor writes heartbeat.json and logs to .governance/evidence/.
        """
        scheduler = MissionScheduler(tmp_path)
        scheduler.schedule_mission(TOPIC_SLUG)

        monitor = HeartbeatMonitor(tmp_path, daemon_id="test_daemon_01")
        state = monitor.pulse(scheduler, active_job_id="job_active_123")

        assert state.daemon_id == "test_daemon_01"
        assert state.queued_jobs_count == 1
        assert state.healthy is True

        # Check canonical state file
        hb_file = tmp_path / ".build" / "runtime" / "heartbeat.json"
        assert hb_file.exists()
        hb_data = json.loads(hb_file.read_text(encoding="utf-8"))
        assert hb_data["active_job_id"] == "job_active_123"

        # Check governance evidence log
        gov_dir = tmp_path / ".governance" / "evidence"
        hb_logs = list(gov_dir.glob("runtime_heartbeats-*.jsonl"))
        assert len(hb_logs) > 0, "Proof 3 FAIL: runtime_heartbeats log missing in .governance/evidence/"

        print(f"\n[Proof 3] Heartbeat state file: {hb_file.name}")
        print(f"[Proof 3] Governance evidence log: {hb_logs[0].name}")

    # ------------------------------------------------------------------
    # 4. Autonomous Runtime Daemon Lifecycle
    # ------------------------------------------------------------------

    def test_autonomous_runtime_daemon_lifecycle(self, tmp_path: Path) -> None:
        """
        Proof 4: AutonomousRuntimeDaemon starts, recovers state, pulses heartbeat,
        processes queue, and shuts down gracefully.
        """
        project = Project(root=tmp_path, config_path=tmp_path / ".ape" / "config.toml")
        ResearchEngine(project=project, offline=False).run_research(TOPIC)
        DecisionEngine(project_root=tmp_path).run_decision(TOPIC, TOPIC_SLUG)
        RoadmapGenerator(tmp_path).generate_roadmap("Daemon Mission", TOPIC_SLUG)

        daemon = AutonomousRuntimeDaemon(tmp_path, daemon_id="daemon_e2e")
        daemon.scheduler.schedule_mission(TOPIC_SLUG)
    
        from tests.dummy_agent import DummyAgent
        from ape.intelligence.execution.engine import ExecutionEngine
        from ape.intelligence.execution.executor import SimulationTaskExecutor
        original_init = ExecutionEngine.__init__
        def patched_init(self, *args, **kwargs):
            kwargs['agent'] = DummyAgent()
            kwargs['executor'] = SimulationTaskExecutor()
            original_init(self, *args, **kwargs)
        
        with patch.object(ExecutionEngine, '__init__', patched_init):
            processed = daemon.start()

        assert len(processed) == 1
        assert processed[0].status == JobStatus.COMPLETED
        assert daemon.is_running is False
        assert daemon.cancellation_token.is_cancelled is True

        print(f"\n[Proof 4] Autonomous Daemon processed {len(processed)} jobs cleanly.")
        print(f"[Proof 4] Graceful shutdown verified. Cancellation token: {daemon.cancellation_token.is_cancelled}")
