"""
Execution Engine — Domain Exceptions.

Separates execution-layer policy failures from generic Python exceptions,
making policy enforcement explicit and testable.
"""
from __future__ import annotations


class PolicyExecutionBlockedError(Exception):
    """
    Raised by ExecutionEngine when a PolicyDecision prevents execution.

    Permitted decisions: BUILD, VALIDATE.
    Blocked decisions:   WATCH, IGNORE, BLOCKED.

    This is the execution-layer analogue of the ValueError raised by
    RoadmapGenerator for the same decisions (RFC-013 / SPEC-0013 §6).
    RFC-014 adds a second gate so that even if `ape plan` is bypassed,
    `ape execute` cannot run on a non-BUILD/VALIDATE decision.
    """


class LineageMismatchError(Exception):
    """
    Raised when the ExecutionState loaded from disk has a different decision_id
    than the currently active Decision artifact.
    Prevents emitting governance events with stale or forged lineage.
    """
