"""
RFC-009: Evidence Partitioning — TDD RED Phase
Testing time-based evidence log partitioning.
"""
import json
from datetime import datetime, timezone
from unittest import mock

from ape.utils import append_to_evidence


def test_evidence_partitioning_creates_ymm_file(tmp_path):
    """Evidence files should be named <track>-YYYY-MM.jsonl based on current time."""
    mock_now = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)
    
    with mock.patch("ape.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        
        # When we append evidence
        append_to_evidence(tmp_path, "execution", {"event": "TEST_START"})
        
        # Then it should be written to execution-2026-07.jsonl
        expected_path = tmp_path / "execution-2026-07.jsonl"
        assert expected_path.exists()
        
        # And NOT execution.jsonl
        assert not (tmp_path / "execution.jsonl").exists()
        
        content = expected_path.read_text(encoding="utf-8")
        assert '{"event": "TEST_START"}' in content


def test_evidence_partitioning_rolls_over_on_new_month(tmp_path):
    """When month changes, a new partition should be created."""
    july_time = datetime(2026, 7, 31, 23, 59, tzinfo=timezone.utc)
    august_time = datetime(2026, 8, 1, 0, 1, tzinfo=timezone.utc)
    
    with mock.patch("ape.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = july_time
        append_to_evidence(tmp_path, "execution", {"event": "JULY_EVENT"})
        
        mock_datetime.now.return_value = august_time
        append_to_evidence(tmp_path, "execution", {"event": "AUGUST_EVENT"})
        
        assert (tmp_path / "execution-2026-07.jsonl").exists()
        assert (tmp_path / "execution-2026-08.jsonl").exists()


def test_evidence_file_is_append_only(tmp_path):
    """The append_to_evidence helper must strictly use 'a' mode and not overwrite past data."""
    mock_now = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)
    with mock.patch("ape.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        
        append_to_evidence(tmp_path, "decisions", {"id": 1})
        append_to_evidence(tmp_path, "decisions", {"id": 2})
        
        content = (tmp_path / "decisions-2026-07.jsonl").read_text(encoding="utf-8")
        lines = [line for line in content.splitlines() if line]
        
        assert len(lines) == 2
        assert json.loads(lines[0])["id"] == 1
        assert json.loads(lines[1])["id"] == 2
