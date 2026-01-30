"""Write content to a file in the workspace (create or overwrite)."""

from pathlib import Path

from langchain_core.tools import tool


@tool
def write_file_tool(file_path: str, content: str, workspace_root: str = ".") -> str:
    """Write content to a file. file_path is relative to workspace_root.
    Creates the file or overwrites it. Use for new files or full-file replacements.
    """
    root = Path(workspace_root).resolve()
    full_path = (root / file_path).resolve()
    try:
        full_path.relative_to(root)
    except ValueError:
        return f"error: file path must be inside workspace: {file_path}"
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
    except Exception as e:
        return f"error: could not write file: {e}"
    return "applied: file written successfully"
