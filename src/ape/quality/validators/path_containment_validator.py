from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from datetime import UTC, datetime, timedelta

from ape.quality.contracts import ValidationContext, ValidationResult, ValidationStatus


class PathContainmentValidator:
    """
    Executable Validator that audits Hermes execution logs for path traversal attempts.
    Wraps tools/security/path_containment_check.py without code duplication.
    Includes freshness filtering to ignore stale evidence logs from prior runs.
    """

    def __init__(self, max_evidence_age_minutes: int = 10) -> None:
        self.default_max_age_minutes = max_evidence_age_minutes

    @property
    def name(self) -> str:
        return "path_containment"

    @property
    def is_critical(self) -> bool:
        return True

    @property
    def weight(self) -> float:
        return 20.0

    def validate(self, context: ValidationContext) -> ValidationResult:
        """Scan Hermes stdout/stderr logs in context for path containment violations."""
        start_time = time.perf_counter()

        if context.dry_run:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.PASS,
                score=100.0,
                duration_ms=0.0,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=["Dry run mode: skipped path containment validation"],
            )

        # Ensure project_root is on sys.path to import tools.security.path_containment_check
        project_root_str = str(context.project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)

        try:
            from tools.security.path_containment_check import evaluate_path_containment
        except ImportError as exc:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                score=0.0,
                duration_ms=(time.perf_counter() - start_time) * 1000.0,
                is_critical=self.is_critical,
                weight=self.weight,
                errors=[f"Could not import tools.security.path_containment_check: {exc}"],
            )

        # Extract allowed_root, freshness limit, and logs from metadata or defaults
        metadata = getattr(context, "metadata", {}) or {}
        allowed_root = str(metadata.get("allowed_root") or context.project_root)
        max_age_minutes = int(metadata.get("max_evidence_age_minutes", self.default_max_age_minutes))

        stdout_content = metadata.get("hermes_stdout") or metadata.get("stdout") or ""
        stderr_content = metadata.get("hermes_stderr") or metadata.get("stderr") or ""

        # If not in metadata, check for file references
        if not stdout_content:
            stdout_file = metadata.get("stdout_file") or metadata.get("transcript_file")
            if stdout_file:
                p = Path(stdout_file)
                if not p.is_absolute():
                    p = context.project_root / p
                if p.exists():
                    stdout_content = p.read_text(encoding="utf-8", errors="ignore")

        if not stderr_content:
            stderr_file = metadata.get("stderr_file")
            if stderr_file:
                p = Path(stderr_file)
                if not p.is_absolute():
                    p = context.project_root / p
                if p.exists():
                    stderr_content = p.read_text(encoding="utf-8", errors="ignore")

        # Read governance evidence .governance/evidence/execution_agent-*.jsonl if still empty
        if not stdout_content and not stderr_content:
            evidence_dir = context.project_root / ".governance" / "evidence"
            now_ts = time.time()
            cutoff_seconds = max_age_minutes * 60

            # Filter evidence files by freshness (mtime within last max_age_minutes)
            agent_logs = []
            if evidence_dir.exists():
                for p in sorted(evidence_dir.glob("execution_agent-*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True):
                    age_sec = now_ts - p.stat().st_mtime
                    if age_sec <= cutoff_seconds:
                        agent_logs.append(p)

            if agent_logs:
                raw_text = agent_logs[0].read_text(encoding="utf-8", errors="ignore")
                log_lines = []
                for line in raw_text.splitlines():
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        # Optionally filter individual JSONL record timestamps if present
                        rec_ts_str = record.get("timestamp")
                        if rec_ts_str:
                            try:
                                rec_dt = datetime.fromisoformat(rec_ts_str.replace("Z", "+00:00"))
                                age = datetime.now(UTC) - rec_dt
                                if age > timedelta(minutes=max_age_minutes):
                                    continue
                            except Exception:
                                pass

                        action = record.get("action")
                        params = record.get("params") or {}
                        stdout_str = record.get("stdout") or ""
                        stderr_str = record.get("stderr") or ""
                        if action and action != "none":
                            log_lines.append(f"Tool call: {action} with args: {json.dumps(params)}")
                        if stdout_str:
                            log_lines.append(f"Stdout: {stdout_str}")
                        if stderr_str:
                            log_lines.append(f"Stderr: {stderr_str}")
                    except Exception:
                        log_lines.append(line)
                stdout_content = "\n".join(log_lines)
            else:
                std_log = context.project_root / ".build" / "quality" / "logs" / "hermes_stdout.log"
                if std_log.exists() and (now_ts - std_log.stat().st_mtime <= cutoff_seconds):
                    stdout_content = std_log.read_text(encoding="utf-8", errors="ignore")

        # Run core containment evaluation
        eval_result = evaluate_path_containment(
            allowed_root=allowed_root,
            stdout_content=stdout_content,
            stderr_content=stderr_content,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Write audit log to .build/quality/logs/
        log_dir = context.project_root / ".build" / "quality" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "path_containment.log"

        violations = eval_result.get("violations", [])
        paths_checked = eval_result.get("paths_checked", [])
        verdict = eval_result.get("verdict", "NO_TOOL_CALLS")

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=== Quality OS Log: path_containment ===\n")
            f.write(f"Allowed Root : {allowed_root}\n")
            f.write(f"Freshness Win: {max_age_minutes} min\n")
            f.write(f"Verdict      : {verdict}\n")
            f.write(f"Tool Calls   : {eval_result.get('total_tool_calls_found', 0)}\n")
            f.write(f"Paths Checked: {len(paths_checked)}\n")
            f.write(f"Violations   : {len(violations)}\n")
            if violations:
                f.write("--- Violations Detail ---\n")
                for v in violations:
                    f.write(f"  Tool: {v.get('tool')}, Path: {v.get('path')} (Resolved: {v.get('normalized_path')})\n")

        logs = {"path_containment.log": str(log_path)}
        metrics = {
            "verdict": verdict,
            "total_tool_calls": eval_result.get("total_tool_calls_found", 0),
            "paths_checked_count": len(paths_checked),
            "violations_count": len(violations),
        }

        # FAIL if any violation is detected
        if verdict == "VIOLATION_DETECTED":
            error_messages = [
                f"Path containment breach: Tool '{v.get('tool')}' accessed '{v.get('path')}' outside allowed root '{allowed_root}'"
                for v in violations
            ]
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                score=0.0,
                duration_ms=duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                errors=error_messages,
                logs=logs,
                metrics=metrics,
            )

        # PASS if contained or no tool calls
        if verdict == "CONTAINED":
            findings = [
                f"Path containment verified: {len(paths_checked)} path(s) checked across {eval_result.get('total_tool_calls_found', 0)} tool calls; zero violations."
            ]
        else:
            findings = [f"No fresh tool call evidence found within last {max_age_minutes} minutes; path containment check passed by default."]

        return ValidationResult(
            validator_name=self.name,
            status=ValidationStatus.PASS,
            score=100.0,
            duration_ms=duration_ms,
            is_critical=self.is_critical,
            weight=self.weight,
            findings=findings,
            logs=logs,
            metrics=metrics,
        )
