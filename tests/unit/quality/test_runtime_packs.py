"""
Unit tests for Pluggable Language Runtime Packs (PR-E1).
"""

from pathlib import Path

from ape.quality.contracts import ValidationContext
from ape.quality.runtime_packs.python_pack import PythonRuntimePack


def test_python_runtime_pack_lifecycle(tmp_path: Path):
    script = tmp_path / "main.py"
    script.write_text("print('hello runtime pack')", encoding="utf-8")

    ctx = ValidationContext(
        project_root=tmp_path,
        topic_slug="test_pack",
        deliverables=["main.py"],
        dry_run=False,
    )

    pack = PythonRuntimePack()
    assert pack.name == "python"

    pack.prepare(ctx)
    proc = pack.launch(ctx)
    passed, msg = pack.probe(ctx)
    pack.shutdown()

    assert passed is True
    assert "PASS" in msg or "executable check" in msg
