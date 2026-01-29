"""Mock tools for the agent: grep, search_replace, shell."""

from src.tools.grep import grep_tool
from src.tools.search_replace import search_replace_tool
from src.tools.shell import run_shell_tool

__all__ = ["grep_tool", "search_replace_tool", "run_shell_tool"]
