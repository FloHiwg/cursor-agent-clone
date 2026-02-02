"""Search-and-replace tool on a single file under workspace_root."""

from pathlib import Path

from langchain_core.tools import tool

from src.tools.diff_utils import ask_user_confirmation, generate_diff


@tool
def search_replace_tool(
    file_path: str,
    old_string: str,
    new_string: str,
    workspace_root: str = ".",
    replace_all: bool = False,
) -> str:
    """Replace old_string with new_string in the given file.
    file_path is relative to workspace_root. old_string must match the file content exactly
    (including newlines and spaces); use read_file first to get the exact text to replace.
    Returns success/failure and whether the patch was applied.
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

    # Generate and display diff, ask for user confirmation
    diff_output = generate_diff(content, new_content, file_path)
    action_desc = f"Replace {'all occurrences' if replace_all else 'first occurrence'} in {file_path}"

    if not ask_user_confirmation(diff_output, action_desc):
        return "rejected: user declined the changes"

    try:
        full_path.write_text(new_content, encoding="utf-8")
    except Exception as e:
        return f"error: could not write file: {e}"
    return "applied: patch written successfully"
