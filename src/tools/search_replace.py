"""Search-and-replace tool on a single file under workspace_root."""

from pathlib import Path

from langchain_core.tools import tool


@tool
def search_replace_tool(
    file_path: str,
    old_string: str,
    new_string: str,
    workspace_root: str = ".",
    replace_all: bool = False,
) -> str:
    """Replace old_string with new_string in the given file (path relative to workspace_root).
    Returns success/failure and whether the patch was applied (for edit accuracy metrics).
    """
    root = Path(workspace_root).resolve()
    full_path = (root / file_path).resolve()
    if not full_path.exists():
        return f"error: file not found: {file_path}"
    if not full_path.is_file():
        return f"error: not a file: {file_path}"
    try:
        content = full_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"error: could not read file: {e}"
    if old_string not in content:
        return "attempted: old_string not found in file (patch not applied)"
    if replace_all:
        new_content = content.replace(old_string, new_string)
    else:
        new_content = content.replace(old_string, new_string, 1)
    try:
        full_path.write_text(new_content, encoding="utf-8")
    except Exception as e:
        return f"error: could not write file: {e}"
    return "applied: patch written successfully"
