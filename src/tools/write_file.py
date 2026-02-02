"""Write content to a file in the workspace (create or overwrite)."""

from pathlib import Path

from langchain_core.tools import tool

from src.tools.diff_utils import (
    ask_user_confirmation,
    generate_diff,
    generate_new_file_preview,
)


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

    # Generate diff or preview and ask for confirmation
    if full_path.exists():
        # File exists - show diff
        try:
            old_content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"error: could not read existing file: {e}"

        diff_output = generate_diff(old_content, content, file_path)
        action_desc = f"Overwrite existing file: {file_path}"
    else:
        # New file - show preview
        diff_output = generate_new_file_preview(content, file_path)
        action_desc = f"Create new file: {file_path}"

    if not ask_user_confirmation(diff_output, action_desc):
        return "rejected: user declined the changes"

    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
    except Exception as e:
        return f"error: could not write file: {e}"
    return "applied: file written successfully"
