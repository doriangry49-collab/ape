"""
ORION-136 — Autonomous Runtime Foundation: Mission Scheduler & Job Queue.

Provides persistent job queue, mission lifecycle management, state recovery,
and execution scheduling on top of the proven APE core.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.pipeline.contracts import ExecutionContext, StageStatus
from ape.pipeline.runner import ConstitutionalPipelineRunner
from ape.runtime.engine import CancellationToken, ExecutionRuntime, RetryPolicy


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


@dataclass
class Job:
    """Represents a scheduled mission task job."""
    job_id: str
    topic_slug: str
    action: str = "full_mission"  # "research" | "decide" | "plan" | "execute" | "full_mission"
    status: JobStatus = JobStatus.QUEUED
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Job:
        d_copy = dict(d)
        if "status" in d_copy and isinstance(d_copy["status"], str):
            d_copy["status"] = JobStatus(d_copy["status"])
        return cls(**d_copy)


class PersistentJobQueue:
    """Manages persistent job queue storage under .build/runtime/jobs.json."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._queue_dir = project_root / ".build" / "runtime"
        self._queue_file = self._queue_dir / "jobs.json"
        self._jobs: Dict[str, Job] = {}
        self._load()

    def _load(self) -> None:
        if self._queue_file.exists():
            try:
                data = json.loads(self._queue_file.read_text(encoding="utf-8"))
                for job_dict in data.get("jobs", []):
                    job = Job.from_dict(job_dict)
                    self._jobs[job.job_id] = job
            except Exception:
                self._jobs = {}

    def _save(self) -> None:
        self._queue_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "job_count": len(self._jobs),
            "jobs": [j.to_dict() for j in self._jobs.values()],
        }
        self._queue_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def enqueue(self, job: Job) -> None:
        self._jobs[job.job_id] = job
        self._save()

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def get_all_jobs(self) -> List[Job]:
        return list(self._jobs.values())

    def get_queued_jobs(self) -> List[Job]:
        return [j for j in self._jobs.values() if j.status == JobStatus.QUEUED]

    def peek_next(self) -> Optional[Job]:
        queued = self.get_queued_jobs()
        if not queued:
            return None
        # Order by created_at
        queued.sort(key=lambda j: j.created_at)
        return queued[0]

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None,
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> Optional[Job]:
        job = self._jobs.get(job_id)
        if not job:
            return None

        job.status = status
        now_str = datetime.now(timezone.utc).isoformat()
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = now_str
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            job.completed_at = now_str

        if error is not None:
            job.error = error

        if metadata_update:
            job.metadata.update(metadata_update)

        self._save()
        return job

    def recover_interrupted_jobs(self) -> List[Job]:
        """
        State recovery: transitions RUNNING jobs back to QUEUED if daemon restarted.
        """
        recovered = []
        for job in self._jobs.values():
            if job.status == JobStatus.RUNNING:
                job.status = JobStatus.QUEUED
                job.metadata["recovered_at"] = datetime.now(timezone.utc).isoformat()
                recovered.append(job)
        if recovered:
            self._save()
        return recovered


class MissionScheduler:
    """
    Schedules and executes missions from the PersistentJobQueue.
    Acts as the bridge between runtime queue management and proven pipeline runners.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self.queue = PersistentJobQueue(project_root)
        self.runtime = ExecutionRuntime(retry_policy=RetryPolicy(max_retries=2))

    def schedule_mission(
        self,
        topic_slug: str,
        action: str = "full_mission",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Job:
        job_id = f"job_{topic_slug}_{int(datetime.now(timezone.utc).timestamp())}"
        job = Job(
            job_id=job_id,
            topic_slug=topic_slug,
            action=action,
            metadata=metadata or {},
        )
        self.queue.enqueue(job)
        return job

    def process_next_job(
        self,
        cancellation_token: Optional[CancellationToken] = None,
        runner_override: Optional[ConstitutionalPipelineRunner] = None,
    ) -> Optional[Job]:
        """
        Pulls next QUEUED job from the queue and executes it.
        Returns the processed Job object with final status.
        """
        job = self.queue.peek_next()
        if not job:
            return None

        self.queue.update_status(job.job_id, JobStatus.RUNNING)

        if cancellation_token and cancellation_token.is_cancelled:
            self.queue.update_status(
                job.job_id, JobStatus.CANCELLED, error="Job cancelled before execution"
            )
            return job

        try:
            job.attempts += 1
            ctx = ExecutionContext(
                run_id=f"sched_{job.job_id}",
                topic_slug=job.topic_slug,
                dry_run=False,
            )

            # Auto-generate roadmap if decision exists but roadmap is missing
            from ape.utils import get_current_artifact
            roadmaps_dir = self._root / ".build" / "roadmaps"
            if not get_current_artifact(roadmaps_dir, job.topic_slug):
                decisions_dir = self._root / ".build" / "decisions"
                if get_current_artifact(decisions_dir, job.topic_slug):
                    from ape.intelligence.roadmap.engine import RoadmapGenerator
                    RoadmapGenerator(self._root).generate_roadmap(job.topic_slug, job.topic_slug)

            if runner_override:
                results = runner_override.run(ctx)
            else:
                # Default pipeline execution
                from ape.intelligence.execution.executor import SimulationTaskExecutor
                from ape.pipeline.stages.capability_check import CapabilityCheckStage
                from ape.pipeline.stages.execution_evidence import ExecutionEvidenceStage
                from ape.pipeline.stages.execution_persist import ExecutionPersistStage
                from ape.pipeline.stages.execution_plan import ExecutionPlanStage
                from ape.pipeline.stages.policy_gate import PolicyGateStage
                from ape.pipeline.stages.release_decision import ReleaseDecisionStage
                from ape.pipeline.stages.task_execution import TaskExecutionStage
                from ape.pipeline.stages.verification import VerificationStage

                runner = ConstitutionalPipelineRunner([
                    ExecutionPlanStage(self._root),
                    PolicyGateStage(self._root),
                    CapabilityCheckStage(self._root),
                    TaskExecutionStage(self._root, executor=SimulationTaskExecutor()),
                    VerificationStage(self._root),
                    ExecutionEvidenceStage(),
                    ExecutionPersistStage(self._root),
                    ReleaseDecisionStage(),
                ])
                results = runner.run(ctx)

            failed_stages = [r for r in results if r.status in (StageStatus.FAILED, StageStatus.BLOCKED)]
            if failed_stages:
                err_msg = f"Stage '{failed_stages[0].stage_name}' failed: {failed_stages[0].error}"
                self.queue.update_status(job.job_id, JobStatus.FAILED, error=err_msg)
            else:
                self.queue.update_status(
                    job.job_id,
                    JobStatus.COMPLETED,
                    metadata_update={"executed_stages_count": len(results)},
                )

        except Exception as exc:
            self.queue.update_status(job.job_id, JobStatus.FAILED, error=str(exc))

        return self.queue.get_job(job.job_id)
