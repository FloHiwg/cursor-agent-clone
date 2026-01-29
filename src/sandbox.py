"""Mock sandbox: run shell commands via subprocess in a given cwd."""

import subprocess
import time
from pathlib import Path


def run_command(command: str, cwd: str | Path | None = None, timeout_seconds: int = 30) -> dict:
    """Run a shell command in cwd. Returns {passed: bool, output: str, duration_ms: int}."""
    cwd = Path(cwd).resolve() if cwd else Path.cwd()
    if not cwd.is_dir():
        return {"passed": False, "output": f"cwd does not exist: {cwd}", "duration_ms": 0}
    start = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        out = (result.stdout or "") + (result.stderr or "")
        return {
            "passed": result.returncode == 0,
            "output": out.strip() or f"(exit code {result.returncode})",
            "duration_ms": duration_ms,
        }
    except subprocess.TimeoutExpired as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return {
            "passed": False,
            "output": f"Timeout after {timeout_seconds}s: {e}",
            "duration_ms": duration_ms,
        }
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return {"passed": False, "output": str(e), "duration_ms": duration_ms}
