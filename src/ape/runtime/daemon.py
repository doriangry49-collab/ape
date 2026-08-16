"""
ORION-136 — Autonomous Runtime Foundation: Daemon & Heartbeat Monitor.

Provides background daemon lifecycle, heartbeat monitoring, graceful shutdown,
and startup state recovery.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.runtime.engine import CancellationToken
from ape.runtime.scheduler import JobStatus, MissionScheduler
from ape.utils import append_to_evidence


@dataclass
class HeartbeatState:
    daemon_id: str
    is_running: bool
    pulse_timestamp: str
    active_job_id: Optional[str]
    queued_jobs_count: int
    completed_jobs_count: int
    failed_jobs_count: int
    healthy: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "daemon_id": self.daemon_id,
            "is_running": self.is_running,
            "pulse_timestamp": self.pulse_timestamp,
            "active_job_id": self.active_job_id,
            "queued_jobs_count": self.queued_jobs_count,
            "completed_jobs_count": self.completed_jobs_count,
            "failed_jobs_count": self.failed_jobs_count,
            "healthy": self.healthy,
        }


class HeartbeatMonitor:
    """Monitors daemon health and logs heartbeat pulses to governance evidence logs."""

    def __init__(self, project_root: Path, daemon_id: str = "ape_daemon_primary") -> None:
        self._root = project_root
        self._daemon_id = daemon_id
        self._runtime_dir = project_root / ".build" / "runtime"
        self._heartbeat_file = self._runtime_dir / "heartbeat.json"

    def pulse(self, scheduler: MissionScheduler, active_job_id: Optional[str] = None) -> HeartbeatState:
        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        all_jobs = scheduler.queue.get_all_jobs()

        queued_count = sum(1 for j in all_jobs if j.status == JobStatus.QUEUED)
        completed_count = sum(1 for j in all_jobs if j.status == JobStatus.COMPLETED)
        failed_count = sum(1 for j in all_jobs if j.status == JobStatus.FAILED)

        state = HeartbeatState(
            daemon_id=self._daemon_id,
            is_running=True,
            pulse_timestamp=datetime.now(timezone.utc).isoformat(),
            active_job_id=active_job_id,
            queued_jobs_count=queued_count,
            completed_jobs_count=completed_count,
            failed_jobs_count=failed_count,
            healthy=True,
        )

        # Write canonical state file
        self._heartbeat_file.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")

        # Append to immutable governance evidence log
        evidence_dir = self._root / ".governance" / "evidence"
        append_to_evidence(evidence_dir, "runtime_heartbeats", state.to_dict())

        return state


class AutonomousRuntimeDaemon:
    """
    Autonomous Runtime Daemon — orchestrates mission queue processing,
    state recovery, heartbeat monitoring, and graceful shutdown.
    """

    def __init__(
        self,
        project_root: Path,
        daemon_id: str = "ape_daemon_primary",
        pulse_interval_seconds: float = 1.0,
    ) -> None:
        self._root = project_root
        self._daemon_id = daemon_id
        self._pulse_interval = pulse_interval_seconds
        self.scheduler = MissionScheduler(project_root)
        self.monitor = HeartbeatMonitor(project_root, daemon_id)
        self.cancellation_token = CancellationToken()
        self.is_running = False

    def start(self) -> List[Any]:
        """
        Starts the daemon, performs startup state recovery, and processes queue.
        Returns list of processed jobs.
        """
        self.is_running = True
        self.cancellation_token.is_cancelled = False

        # 1. Startup State Recovery
        recovered = self.scheduler.queue.recover_interrupted_jobs()

        processed_jobs = []

        # 2. Process Queue Loop
        try:
            while self.is_running and not self.cancellation_token.is_cancelled:
                next_job = self.scheduler.queue.peek_next()
                active_id = next_job.job_id if next_job else None

                # Pulse heartbeat
                self.monitor.pulse(self.scheduler, active_job_id=active_id)

                if not next_job:
                    # No jobs in queue, stop single-pass or wait in daemon mode
                    break

                # Process next job
                processed = self.scheduler.process_next_job(
                    cancellation_token=self.cancellation_token
                )
                if processed:
                    processed_jobs.append(processed)

        finally:
            self.stop()

        return processed_jobs

    def stop(self) -> None:
        """Triggers graceful shutdown."""
        self.is_running = False
        self.cancellation_token.cancel()
        # Final heartbeat pulse reflecting stopped status
        if self._heartbeat_file_exists():
            state_dict = {
                "daemon_id": self._daemon_id,
                "is_running": False,
                "pulse_timestamp": datetime.now(timezone.utc).isoformat(),
                "active_job_id": None,
                "queued_jobs_count": 0,
                "completed_jobs_count": 0,
                "failed_jobs_count": 0,
                "healthy": True,
            }
            (self._root / ".build" / "runtime" / "heartbeat.json").write_text(
                json.dumps(state_dict, indent=2), encoding="utf-8"
            )

    def _heartbeat_file_exists(self) -> bool:
        return (self._root / ".build" / "runtime" / "heartbeat.json").exists()
