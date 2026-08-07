"""
ExecutionRequest & ExecutionMode Specification — ORION-115.
Defines rich ExecutionMode enum and ExecutionRequest value object.
"""

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict, Optional

from ape.capabilities.budget import ExecutionBudget
from ape.capabilities.contracts import ExecutionContext, ExecutionPolicy
from ape.prompts.template import RenderedPrompt


class ExecutionMode(str, Enum):
    """Execution request processing mode classification."""
    SYNC = "sync"
    STREAM = "stream"
    BATCH = "batch"
    TOOL = "tool"
    AGENT = "agent"


@dataclass(frozen=True)
class ExecutionRequest:
    """Rich execution request contract encapsulating capability, prompt, context, policy, and budget."""
    request_id: str
    capability_id: str
    rendered_prompt: RenderedPrompt
    context: ExecutionContext
    mode: ExecutionMode = ExecutionMode.SYNC
    policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    budget: ExecutionBudget = field(default_factory=ExecutionBudget)
    deadline: Optional[float] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
