"""
Execution Engine — Deterministic Runtime Evaluators & Health Signals.
ORION-123 (Mission B) Specification.

Provides non-LLM, 100% deterministic evaluation logic that consumes normalized
ExecutionTrajectory streams and emits risk-calibrated ExecutionHealthSignals.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ape.intelligence.execution.trajectory import ExecutionTrajectory, TrajectoryStep


class SignalSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ExecutionHealthSignal:
    """
    Deterministic health signal emitted by a supervisory runtime evaluator.
    Contains evaluation metadata, pattern signatures, and evidence references.
    """
    signal_type: str
    severity: SignalSeverity
    confidence: float
    signature: str
    task_id: str
    evidence_ref: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "signature": self.signature,
            "task_id": self.task_id,
            "evidence_ref": self.evidence_ref,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ExecutionHealthSignal:
        return cls(
            signal_type=str(d.get("signal_type", "")),
            severity=SignalSeverity(d.get("severity", "LOW")),
            confidence=float(d.get("confidence", 1.0)),
            signature=str(d.get("signature", "")),
            task_id=str(d.get("task_id", "")),
            evidence_ref=str(d.get("evidence_ref", "")),
            message=str(d.get("message", "")),
        )


class BaseRuntimeEvaluator(abc.ABC):
    """Abstract interface for deterministic trajectory evaluators."""

    @abc.abstractmethod
    def evaluate(self, trajectory: ExecutionTrajectory) -> List[ExecutionHealthSignal]:
        """Consumes an ExecutionTrajectory and returns health signals."""
        pass


class RepeatedErrorEvaluator(BaseRuntimeEvaluator):
    """
    Detects repeated identical error signatures for a task.
    Triggers CRITICAL REPEATED_ERROR signal if same error repeats >= 3 times.
    """

    def __init__(self, threshold: int = 3) -> None:
        self._threshold = threshold

    def evaluate(self, trajectory: ExecutionTrajectory) -> List[ExecutionHealthSignal]:
        signals: List[ExecutionHealthSignal] = []

        # Group steps by task_id
        tasks_map: Dict[str, List[TrajectoryStep]] = {}
        for step in trajectory.steps:
            tasks_map.setdefault(step.task_id, []).append(step)

        for task_id, steps in tasks_map.items():
            error_counts: Dict[str, List[TrajectoryStep]] = {}
            for s in steps:
                if s.stderr_signature:
                    error_counts.setdefault(s.stderr_signature, []).append(s)

            for sig, occurrences in error_counts.items():
                if len(occurrences) >= self._threshold:
                    last_step = occurrences[-1]
                    msg = (
                        f"Task '{task_id}' encountered repeated error signature "
                        f"'{sig}' across {len(occurrences)} attempts."
                    )
                    signals.append(
                        ExecutionHealthSignal(
                            signal_type="REPEATED_ERROR",
                            severity=SignalSeverity.CRITICAL,
                            confidence=1.0,
                            signature=sig,
                            task_id=task_id,
                            evidence_ref=last_step.step_id,
                            message=msg,
                        )
                    )

        return signals


class LoopEvaluator(BaseRuntimeEvaluator):
    """
    Detects repeating action-parameter ping-pong cycles (e.g. A -> B -> A -> B).
    Triggers HIGH ACTION_LOOP signal when cycle repeats >= 2 times.
    """

    def __init__(self, min_cycle: int = 2) -> None:
        self._min_cycle = min_cycle

    def evaluate(self, trajectory: ExecutionTrajectory) -> List[ExecutionHealthSignal]:
        signals: List[ExecutionHealthSignal] = []

        tasks_map: Dict[str, List[TrajectoryStep]] = {}
        for step in trajectory.steps:
            tasks_map.setdefault(step.task_id, []).append(step)

        for task_id, steps in tasks_map.items():
            actions = [f"{s.action}:{str(s.params)}" for s in steps]
            if len(actions) < 4:
                continue

            # Detect alternating 2-pattern cycles (A, B, A, B)
            for i in range(len(actions) - 3):
                if actions[i] == actions[i + 2] and actions[i + 1] == actions[i + 3]:
                    cycle_sig = f"{actions[i]} <-> {actions[i + 1]}"
                    last_step = steps[i + 3]
                    msg = (
                        f"Task '{task_id}' detected alternating action ping-pong cycle: "
                        f"'{cycle_sig}'."
                    )
                    signals.append(
                        ExecutionHealthSignal(
                            signal_type="ACTION_LOOP",
                            severity=SignalSeverity.HIGH,
                            confidence=1.0,
                            signature=cycle_sig,
                            task_id=task_id,
                            evidence_ref=last_step.step_id,
                            message=msg,
                        )
                    )
                    break

        return signals


class ProgressEvaluator(BaseRuntimeEvaluator):
    """
    Detects execution stagnation where step count increases without status progress.
    Triggers MEDIUM NO_PROGRESS signal if >= 3 steps execute without completion.
    """

    def __init__(self, max_stagnant_steps: int = 3) -> None:
        self._max_stagnant_steps = max_stagnant_steps

    def evaluate(self, trajectory: ExecutionTrajectory) -> List[ExecutionHealthSignal]:
        signals: List[ExecutionHealthSignal] = []

        tasks_map: Dict[str, List[TrajectoryStep]] = {}
        for step in trajectory.steps:
            tasks_map.setdefault(step.task_id, []).append(step)

        for task_id, steps in tasks_map.items():
            non_success_steps = [s for s in steps if s.status != "COMPLETED"]
            if len(non_success_steps) >= self._max_stagnant_steps:
                last_step = non_success_steps[-1]
                msg = (
                    f"Task '{task_id}' stagnated across {len(non_success_steps)} "
                    f"steps without successful status completion."
                )
                signals.append(
                    ExecutionHealthSignal(
                        signal_type="NO_PROGRESS",
                        severity=SignalSeverity.MEDIUM,
                        confidence=1.0,
                        signature=f"stagnation_{len(non_success_steps)}_steps",
                        task_id=task_id,
                        evidence_ref=last_step.step_id,
                        message=msg,
                    )
                )

        return signals


class BudgetBurnEvaluator(BaseRuntimeEvaluator):
    """
    Evaluates execution wall-clock time against budget limits.
    Emits HIGH BUDGET_WARNING signal if trajectory total duration exceeds max_seconds.
    """

    def __init__(self, max_seconds: float = 300.0) -> None:
        self._max_seconds = max_seconds

    def evaluate(self, trajectory: ExecutionTrajectory) -> List[ExecutionHealthSignal]:
        signals: List[ExecutionHealthSignal] = []

        if len(trajectory.steps) < 2:
            return signals

        # Parse timestamps of first and last step
        try:
            from datetime import datetime
            t_first = datetime.fromisoformat(trajectory.steps[0].timestamp)
            t_last = datetime.fromisoformat(trajectory.steps[-1].timestamp)
            duration = (t_last - t_first).total_seconds()

            if duration > self._max_seconds:
                msg = (
                    f"Trajectory duration ({duration:.1f}s) exceeded wall-clock "
                    f"budget limit ({self._max_seconds:.1f}s)."
                )
                signals.append(
                    ExecutionHealthSignal(
                        signal_type="BUDGET_WARNING",
                        severity=SignalSeverity.HIGH,
                        confidence=1.0,
                        signature=f"latency_exceeded_{int(duration)}s",
                        task_id="engine",
                        evidence_ref=trajectory.steps[-1].step_id,
                        message=msg,
                    )
                )
        except Exception:
            pass

        return signals


class CompositeRuntimeEvaluator(BaseRuntimeEvaluator):
    """
    Aggregates multiple deterministic evaluators into a unified evaluation pass.
    """

    def __init__(self, evaluators: Optional[List[BaseRuntimeEvaluator]] = None) -> None:
        self.evaluators = evaluators or [
            RepeatedErrorEvaluator(),
            LoopEvaluator(),
            ProgressEvaluator(),
            BudgetBurnEvaluator(),
        ]

    def evaluate(self, trajectory: ExecutionTrajectory) -> List[ExecutionHealthSignal]:
        all_signals: List[ExecutionHealthSignal] = []
        for evaluator in self.evaluators:
            try:
                signals = evaluator.evaluate(trajectory)
                all_signals.extend(signals)
            except Exception as exc:
                # Fail-closed evaluator error handling
                all_signals.append(
                    ExecutionHealthSignal(
                        signal_type="EVALUATOR_ERROR",
                        severity=SignalSeverity.CRITICAL,
                        confidence=1.0,
                        signature=f"eval_error_{evaluator.__class__.__name__}",
                        task_id="engine",
                        evidence_ref="evaluator",
                        message=f"Evaluator '{evaluator.__class__.__name__}' failed: {exc}",
                    )
                )
        return all_signals
