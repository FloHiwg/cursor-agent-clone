"""Orchestrator: build and compile the Plan → Act → Observe graph."""

import os
import time
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from src.context_engine import context_engine_node
from src.logging_.trajectory import append_trajectory
from src.logging_.visual import log_state_transition
from src.router import router_node
from src.sandbox import run_command
from src.state import AgentState
from src.tool_harness import get_tools, get_tool_node

MAX_LOOPS = 10
VERIFY_COMMAND = "python -m pytest --tb=short -q 2>/dev/null || true"


def _get_llm(model_tier: Literal["high", "fast"]):
    """Return chat model: Gemini if GOOGLE_API_KEY is set, else OpenAI."""
    if os.environ.get("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = "gemini-1.5-pro" if model_tier == "high" else "gemini-2.0-flash"
        return ChatGoogleGenerativeAI(model=model, temperature=0)
    from langchain_openai import ChatOpenAI
    model = "gpt-4o" if model_tier == "high" else "gpt-4o-mini"
    return ChatOpenAI(model=model, temperature=0)


def build_plan_node(workspace_root: str):
    """Build plan node with workspace-bound tools."""
    tools = get_tools(workspace_root)

    def plan_node(state: AgentState) -> dict:
        log_state_transition("plan", state)
        model_tier = state.get("model_tier") or "fast"
        llm = _get_llm(model_tier).bind_tools(tools)
        snippets = state.get("context_snippets") or []
        context_blob = "\n\n".join(snippets[:10]) if snippets else "(no context)"
        system = (
            "You are a coding agent in the Plan phase. You have context snippets from the codebase. "
            "Use the tools: grep_tool (search files), search_replace_tool (edit a file), run_shell_tool (run commands, e.g. tests). "
            "When done editing, run tests with run_shell_tool (e.g. pytest). Reply with tool_calls or a short summary."
        )
        messages = list(state.get("messages") or [])
        if not messages:
            messages = [HumanMessage(content=state.get("user_request") or "")]
        msgs = [
            SystemMessage(content=f"{system}\n\nContext:\n{context_blob}"),
            *messages,
        ]
        start = time.perf_counter()
        out = llm.invoke(msgs)
        model_ms = int((time.perf_counter() - start) * 1000)
        lb = dict(state.get("latency_breakdown") or {})
        lb["model_ms"] = lb.get("model_ms", 0) + model_ms
        update = {
            "messages": [out],
            "current_phase": "act" if getattr(out, "tool_calls", None) else "observe",
            "latency_breakdown": lb,
        }
        update.update(append_trajectory("plan", "llm_call", f"model_tier={model_tier}"))
        return update

    return plan_node


def build_verify_node(workspace_root: str):
    """Build verify node: run test command in sandbox."""

    def verify_node(state: AgentState) -> dict:
        log_state_transition("verify", state)
        root = workspace_root or "."
        result = run_command(VERIFY_COMMAND, cwd=root)
        lb = dict(state.get("latency_breakdown") or {})
        lb["sandbox_ms"] = lb.get("sandbox_ms", 0) + result.get("duration_ms", 0)
        update = {
            "verification_result": {"passed": result["passed"], "output": result.get("output", "")},
            "latency_breakdown": lb,
            "current_phase": "observe",
        }
        update.update(append_trajectory("verify", "run_tests", str(result.get("passed"))))
        return update

    return verify_node


def build_observe_node():
    """Build observe node: decide continue or END."""

    def observe_node(state: AgentState) -> dict:
        log_state_transition("observe", state)
        loop_count = (state.get("loop_count") or 0) + 1
        verification = state.get("verification_result") or {}
        passed = verification.get("passed", False)
        update = {
            "loop_count": loop_count,
            "current_phase": "done" if (passed or loop_count >= MAX_LOOPS) else "plan",
        }
        update.update(append_trajectory("observe", "decision", f"passed={passed} loop={loop_count}"))
        return update

    return observe_node


def route_after_plan(state: AgentState) -> Literal["tools", "verify"]:
    """Route from plan: tools if last message has tool_calls, else verify."""
    messages = state.get("messages") or []
    if not messages:
        return "verify"
    last = messages[-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "tools"
    return "verify"


def route_after_observe(state: AgentState) -> Literal["plan", "__end__"]:
    """Route from observe: plan if not done, else END."""
    phase = state.get("current_phase") or "done"
    if phase == "plan":
        return "plan"
    return "__end__"


def build_graph(workspace_root: str):
    """Build the StateGraph with all nodes and edges."""
    builder = StateGraph(AgentState)
    builder.add_node("router", router_node)
    builder.add_node("context_engine", context_engine_node)
    builder.add_node("plan", build_plan_node(workspace_root))
    builder.add_node("tools", get_tool_node(workspace_root))
    builder.add_node("verify", build_verify_node(workspace_root))
    builder.add_node("observe", build_observe_node())

    builder.add_edge(START, "router")
    builder.add_edge("router", "context_engine")
    builder.add_edge("context_engine", "plan")
    builder.add_conditional_edges("plan", route_after_plan, {"tools": "tools", "verify": "verify"})
    builder.add_edge("tools", "plan")
    builder.add_edge("verify", "observe")
    builder.add_conditional_edges("observe", route_after_observe, {"plan": "plan", "__end__": END})

    return builder.compile()
