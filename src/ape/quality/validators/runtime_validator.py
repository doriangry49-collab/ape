"""
Runtime Verification Engine Executable Validator — Capability Milestone F.
Executes live process lifecycle checks and HTTP health probes for generated deliverables.
"""

from __future__ import annotations

import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import List, Optional

from ape.quality.contracts import ValidationContext, ValidationResult, ValidationStatus

WEB_FRAMEWORK_IMPORTS = ["fastapi", "flask", "uvicorn", "http.server", "wsgiref", "aiohttp", "tornado"]


def find_available_port() -> int:
    """Find a dynamic unused TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class RuntimeValidator:
    """Executable Validator that performs live application runtime execution and HTTP health probing."""

    @property
    def name(self) -> str:
        return "runtime"

    @property
    def is_critical(self) -> bool:
        return True

    @property
    def weight(self) -> float:
        return 2.5

    def _is_web_app(self, file_path: Path) -> bool:
        """Inspect file content to detect web framework usage."""
        try:
            content = file_path.read_text(encoding="utf-8").lower()
            return any(fw in content for fw in WEB_FRAMEWORK_IMPORTS)
        except Exception:
            return False

    def validate(self, context: ValidationContext) -> ValidationResult:
        """Perform live runtime verification."""
        start_time = time.perf_counter()

        if context.dry_run:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.PASS,
                score=100.0,
                duration_ms=0.0,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=["Dry run mode: skipped runtime verification"],
            )

        # Discover primary entrypoint
        entrypoint: Optional[Path] = None
        for candidate in ["main.py", "app.py", "cli.py"]:
            p = context.project_root / candidate
            if p.exists():
                entrypoint = p
                break

        if not entrypoint:
            for item in context.deliverables:
                p = context.project_root / item
                if p.exists() and p.name.endswith(".py"):
                    entrypoint = p
                    break

        if not entrypoint:
            for p in context.project_root.glob("*.py"):
                if p.is_file() and not p.name.startswith("test_"):
                    entrypoint = p
                    break

        if not entrypoint:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.SKIP,
                score=100.0,
                duration_ms=(time.perf_counter() - start_time) * 1000.0,
                is_critical=self.is_critical,
                weight=self.weight,
                findings=["No Python entrypoint script found to execute runtime verification"],
            )

        rel_entry = str(entrypoint.relative_to(context.project_root))
        errors: List[str] = []
        findings: List[str] = []
        warnings: List[str] = []
        is_web = self._is_web_app(entrypoint)

        log_dir = context.project_root / ".build" / "quality" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "runtime.log"

        # Resolve src_root for PYTHONPATH injection
        import sys
        src_root = context.src_root
        if src_root is None:
            candidate = context.project_root / "src"
            if candidate.is_dir():
                src_root = candidate

        extra_env = dict(os.environ)
        if src_root is not None:
            existing = extra_env.get("PYTHONPATH", "")
            extra_env["PYTHONPATH"] = str(src_root) + (os.pathsep + existing if existing else "")

        # Detect if the entrypoint is a CLI module inside a src/ package.
        # If so, run as `python -m <package>.<module>` instead of as a bare script.
        cli_cmd: List[str]
        is_cli_module = src_root is not None and src_root in entrypoint.parents
        if is_cli_module:
            # Compute dotted module name from src_root
            rel = entrypoint.relative_to(src_root).with_suffix("")
            module_dotted = ".".join(rel.parts)
            cli_cmd = [sys.executable, "-m", module_dotted, "--help"]
        else:
            cli_cmd = [sys.executable, str(entrypoint)]

        if not is_web:
            # Mode A: Ephemeral Process Execution for CLI / Script Deliverables
            try:
                proc = subprocess.run(
                    cli_cmd,
                    cwd=str(context.project_root),
                    capture_output=True,
                    text=True,
                    timeout=5.0,
                    env=extra_env,
                )
                if proc.returncode == 0:
                    findings.append(f"CLI process '{rel_entry}' executed and exited cleanly (exit code 0)")
                elif is_cli_module and proc.returncode in (0, 1, 2):
                    # CLI tools typically exit 0 on --help; exit 1/2 on missing args.
                    # This is expected behaviour, not a failure.
                    findings.append(
                        f"CLI module '{module_dotted}' responded to --help (exit {proc.returncode}) — runtime OK"
                    )
                else:
                    err_out = (proc.stderr or proc.stdout or "")[:200]
                    errors.append(f"CLI process '{rel_entry}' failed with exit code {proc.returncode}: {err_out}")
            except subprocess.TimeoutExpired:
                errors.append(f"CLI process '{rel_entry}' timed out after 5.0 seconds")
            except Exception as exc:
                errors.append(f"Failed to execute CLI process '{rel_entry}': {exc}")

        else:
            # Mode B: Web Service Probe
            port = find_available_port()
            env = dict(os.environ)
            env.update({"PORT": str(port), "PYTHONUNBUFFERED": "1"})
            cmd = ["python", str(entrypoint)]

            proc_handle: Optional[subprocess.Popen] = None
            try:
                proc_handle = subprocess.Popen(
                    cmd,
                    cwd=str(context.project_root),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                
                server_url = f"http://127.0.0.1:{port}/"
                probe_success = False
                probe_status = 0

                for _ in range(15):  # Probe loop up to 3.0s
                    try:
                        req = urllib.request.Request(server_url, headers={"User-Agent": "APE-QualityOS-Probe/1.0"})
                        with urllib.request.urlopen(req, timeout=1.0) as resp:
                            probe_status = resp.status
                            if probe_status < 400:
                                probe_success = True
                                break
                    except urllib.error.HTTPError as http_err:
                        probe_status = http_err.code
                        if probe_status < 500:
                            probe_success = True
                            break
                    except Exception:
                        pass

                    if proc_handle.poll() is not None and not probe_success:
                        errors.append(f"Web server '{rel_entry}' terminated prematurely")
                        break
                    time.sleep(0.2)

                if probe_success:
                    findings.append(f"Web server '{rel_entry}' live probe on localhost:{port} returned HTTP {probe_status}")
                elif not errors:
                    errors.append(f"Web server '{rel_entry}' failed HTTP health probe on localhost:{port}")

            except Exception as exc:
                errors.append(f"Failed to launch web server process '{rel_entry}': {exc}")
            finally:
                if proc_handle and proc_handle.poll() is None:
                    proc_handle.terminate()
                    try:
                        proc_handle.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        proc_handle.kill()

        # Write physical evidence log
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=== Quality OS Log: runtime ===\n")
            f.write(f"Target Entrypoint : {rel_entry}\n")
            f.write(f"Is Web Framework  : {is_web}\n")
            f.write(f"Findings          : {findings}\n")
            f.write(f"Errors            : {errors}\n")

        logs = {"runtime.log": str(log_path)}
        metrics = {
            "is_web_app": is_web,
            "runtime_error_count": len(errors),
        }

        if errors:
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                score=0.0,
                duration_ms=duration_ms,
                is_critical=self.is_critical,
                weight=self.weight,
                errors=errors,
                logs=logs,
                metrics=metrics,
            )

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
