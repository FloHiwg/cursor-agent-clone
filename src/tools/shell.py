"""Shell/terminal tool that delegates to the sandbox."""

from langchain_core.tools import tool


def _get_sandbox_run():
    """Lazy import to avoid circular dependency."""
    from src.sandbox import run_command
    return run_command


@tool
def run_shell_tool(
    command: str,
    cwd: str = ".",
    workspace_root: str = ".",
) -> str:
    """Run a shell command in the workspace directory. Use for builds and tests (e.g. pytest, npm test)."""
    from pathlib import Path
    root = Path(workspace_root).resolve()
    work_dir = (root / cwd).resolve() if cwd != "." else root
    run_command = _get_sandbox_run()
    result = run_command(command, cwd=str(work_dir))
    output = result.get("output", "")
    passed = result.get("passed", False)
    return f"exit_ok={passed}\n{output}"
