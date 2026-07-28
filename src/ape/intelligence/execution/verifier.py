"""
Deliverable Verifier — deterministic, no network, no LLM.

MVP rule: a task is VERIFIED if all declared deliverable paths exist on disk.
In dry-run mode, verification is skipped (nothing was created).
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple


class DeliverableVerifier:
    def __init__(self, project_root: Path, dry_run: bool = True) -> None:
        self._root = project_root
        self._dry_run = dry_run

    def verify(self, deliverables: list[str]) -> Tuple[bool, list[str]]:
        """
        Returns (ok, missing_items).
        In dry-run mode always returns (True, []) — nothing was produced.
        """
        if self._dry_run or not deliverables:
            return True, []

        missing = [d for d in deliverables if not (self._root / d).exists()]
        return (len(missing) == 0), missing
