"""Tool harness: build workspace-bound tools and ToolNode for the graph."""

from typing import TYPE_CHECKING

from langchain_core.tools import StructuredTool
from langgraph.prebuilt import ToolNode

from src.tools.grep import grep_tool
from src.tools.shell import run_shell_tool
from src.tools.search_replace import search_replace_tool

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


def _bind_workspace(tool: "BaseTool", workspace: str) -> "BaseTool":
    """Wrap a tool so that workspace_root is always set to workspace when invoked."""
    def invoker(**kwargs):
        kwargs["workspace_root"] = workspace
        return tool.invoke(kwargs)
    return StructuredTool.from_function(
        func=invoker,
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
    )


def get_tools(workspace_root: str) -> list["BaseTool"]:
    """Return tools with workspace_root bound (for use in the graph)."""
    root = workspace_root or "."
    return [
        _bind_workspace(grep_tool, root),
        _bind_workspace(search_replace_tool, root),
        _bind_workspace(run_shell_tool, root),
    ]


def get_tool_node(workspace_root: str) -> ToolNode:
    """Return a ToolNode that runs the workspace-bound tools."""
    return ToolNode(get_tools(workspace_root))
