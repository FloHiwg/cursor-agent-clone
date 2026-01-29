"""Grep/search tool over files in a workspace directory."""

import re
from pathlib import Path

from langchain_core.tools import tool


@tool
def grep_tool(
    pattern: str,
    path: str = ".",
    workspace_root: str = ".",
) -> str:
    """Search for a pattern in files under the given path (relative to workspace_root).
    Returns matching lines with file:line content.
    """
    root = Path(workspace_root).resolve()
    search_path = (root / path).resolve()
    if not search_path.exists():
        return f"Path does not exist: {search_path}"
    if not search_path.is_dir():
        return f"Not a directory: {search_path}"
    try:
        regex = re.compile(pattern)
    except re.error:
        # Fallback to substring search
        regex = None
    results: list[str] = []
    for f in search_path.rglob("*"):
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            results.append(f"{f.relative_to(root)}: (read error: {e})")
            continue
        rel = f.relative_to(root)
        for i, line in enumerate(text.splitlines(), 1):
            if regex:
                if regex.search(line):
                    results.append(f"{rel}:{i}: {line.strip()}")
            else:
                if pattern in line:
                    results.append(f"{rel}:{i}: {line.strip()}")
    if not results:
        return f"No matches for pattern '{pattern}' under {path}"
    return "\n".join(results[:100])
