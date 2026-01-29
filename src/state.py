"""Graph state schema and reducers for the agentic loop."""

from operator import add
from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State for the Plan → Act → Observe graph."""

    messages: Annotated[list, add_messages]
    user_request: str
    workspace_path: str
    loop_count: int
    model_tier: Literal["high", "fast"]
    current_phase: Literal["plan", "retrieve", "act", "verify", "observe", "done"]
    context_snippets: list[str]
    verification_result: dict
    trajectory: Annotated[list[dict], add]
    edit_attempts: int
    edit_applied: int
    latency_breakdown: dict
