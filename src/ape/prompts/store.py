"""
Isolated Prompt Trace Storage — ORION-111A Specification.
Saves detailed PromptTrace JSON records under .build/ventures/{venture_id}/traces/prompt/{trace_id}.json.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ape.prompts.template import PromptTrace


class PromptTraceStore:
    """Manages isolated prompt trace JSON files inside .build/ventures/{venture_id}/traces/prompt/."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root_dir = Path(root_dir) if root_dir else Path(".build/ventures")

    def get_trace_path(self, venture_id: str, trace_id: str) -> Path:
        """Return path to trace JSON file."""
        return self.root_dir / venture_id / "traces" / "prompt" / f"{trace_id}.json"

    def save_trace(self, venture_id: str, trace: PromptTrace) -> Path:
        """Save a PromptTrace record to disk."""
        trace_path = self.get_trace_path(venture_id, trace.trace_id)
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(json.dumps(trace.to_dict(), indent=2), encoding="utf-8")
        return trace_path

    def load_trace(self, venture_id: str, trace_id: str) -> Optional[Dict[str, Any]]:
        """Load a PromptTrace record if exists."""
        trace_path = self.get_trace_path(venture_id, trace_id)
        if not trace_path.exists():
            return None
        return json.loads(trace_path.read_text(encoding="utf-8"))
