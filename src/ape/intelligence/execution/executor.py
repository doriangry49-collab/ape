"""
Task Executor — abstract boundary + simulation-first MVP implementation.

DEFAULT = SIMULATION (dry_run=True).
Real shell execution is wired but NEVER the default in MVP.
No LLM provider dependency.
"""
from __future__ import annotations

import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass


class TaskExecutor(ABC):
    """Abstract executor boundary. Engine talks only to this interface."""

    @abstractmethod
    def execute(self, task_description: str, deliverables: list[str]) -> str:
        """Execute a task. Returns a human-readable result string."""


class SimulationTaskExecutor(TaskExecutor):
    """
    MVP default executor — simulation mode.
    Prints what it would do; creates NO real files or processes.
    This is the ONLY executor used in Sprint 12 MVP.
    """

    def execute(self, task_description: str, deliverables: list[str]) -> str:
        return f"[SIMULATED] Would execute: {task_description}"


@dataclass
class SandboxResult:
    exit_code: int
    output: str
    error: str
    status: str


class DockerSandboxExecutor(TaskExecutor):
    """
    Real executor utilizing a Docker sandbox.
    Fails closed if Docker is unavailable.
    Applies strict constraints: network=none, resource limits, clean env.
    """

    def execute(self, task_description: str, deliverables: list[str]) -> str:
        result = self.execute_command("echo " + task_description, cwd="/tmp")
        if result.status == "BLOCKED":
            raise RuntimeError(f"Docker unavailable. Sandbox execution blocked: {result.error}")
        if result.exit_code != 0:
            raise RuntimeError(f"Sandbox Error: {result.error}")
        return result.output

    def execute_command(self, cmd: str, cwd: str, timeout: int = 60) -> SandboxResult:
        if not shutil.which("docker"):
            return SandboxResult(
                exit_code=-1,
                output="",
                error="Docker unavailable. Sandbox execution blocked.",
                status="BLOCKED"
            )
        
        # Build strict docker command
        docker_cmd = [
            "docker", "run", "--rm",
            "--network=none",
            "--memory=512m",
            "--cpus=1.0",
            "-w", cwd,
            "alpine", "sh", "-c", cmd
        ]
        
        try:
            # We explicitly do NOT pass host environment (env=None)
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={}  # No host env vars
            )
            status = "COMPLETED" if proc.returncode == 0 else "FAILED"
            return SandboxResult(
                exit_code=proc.returncode,
                output=proc.stdout,
                error=proc.stderr,
                status=status
            )
        except subprocess.TimeoutExpired as e:
            return SandboxResult(
                exit_code=-1,
                output="",
                error=f"Execution timed out: {str(e)}",
                status="FAILED"
            )
        except Exception as e:
            return SandboxResult(
                exit_code=-1,
                output="",
                error=f"Execution failed: {str(e)}",
                status="FAILED"
            )
