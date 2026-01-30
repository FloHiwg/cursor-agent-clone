"""Read a file's contents from the workspace."""

from pathlib import Path

from langchain_core.tools import tool


@tool
def read_file_tool(file_path: str, workspace_root: str = ".") -> str:
    """Read the contents of a file. file_path is relative to workspace_root.
    Use this before editing so you have the exact text for search_replace.
    """
    root = Path(workspace_root).resolve()
    full_path = (root / file_path).resolve()
    if not full_path.exists():
        return f"error: file not found: {file_path}"
    if not full_path.is_file():
        return f"error: not a file: {file_path}"
    try:
        return full_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"error: could not read file: {e}"
