#!/usr/bin/env python3
"""CLI entry: invoke the agentic graph with a user request."""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from langchain_core.messages import HumanMessage

from src.logging_.visual import print_summary, print_trajectory_table
from src.orchestrator import build_graph

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the coding agent PoC (Plan → Act → Observe)")
    parser.add_argument("request", nargs="?", default="List all Python files in the workspace", help="User request")
    parser.add_argument("--workspace", "-w", default="./workspace", help="Workspace directory (default: ./workspace)")
    parser.add_argument("--recursion-limit", type=int, default=20, help="Max graph steps (default: 20)")
    args = parser.parse_args()
    workspace_path = Path(args.workspace).resolve()
    workspace_path.mkdir(parents=True, exist_ok=True)
    graph = build_graph(str(workspace_path))
    initial = {
        "user_request": args.request,
        "workspace_path": str(workspace_path),
        "messages": [HumanMessage(content=args.request)],
        "loop_count": 0,
        "current_phase": "plan",
        "context_snippets": [],
        "verification_result": {},
        "trajectory": [],
        "edit_attempts": 0,
        "edit_applied": 0,
        "latency_breakdown": {},
    }
    config = {"recursion_limit": args.recursion_limit}
    result = graph.invoke(initial, config=config)
    print_summary(result)
    print_trajectory_table(result.get("trajectory") or [], last_n=15)


if __name__ == "__main__":
    main()
