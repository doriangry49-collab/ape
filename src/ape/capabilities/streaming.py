"""
Streaming Execution Engine — ORION-114 Specification.
Provides StreamChunk model and streaming iterators for real-time provider execution.
"""

from dataclasses import dataclass
from typing import Optional

from ape.capabilities.contracts import FinishReason


@dataclass(frozen=True)
class StreamChunk:
    """Immutable real-time execution stream token chunk payload."""
    delta_text: str
    index: int = 0
    finish_reason: Optional[FinishReason] = None
    token_count: int = 1
