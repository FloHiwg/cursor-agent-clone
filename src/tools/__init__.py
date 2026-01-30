"""Mock tools for the agent: grep, read_file, search_replace, write_file, shell."""

from src.tools.grep import grep_tool
from src.tools.read_file import read_file_tool
from src.tools.search_replace import search_replace_tool
from src.tools.shell import run_shell_tool
from src.tools.write_file import write_file_tool

__all__ = ["grep_tool", "read_file_tool", "search_replace_tool", "write_file_tool", "run_shell_tool"]
