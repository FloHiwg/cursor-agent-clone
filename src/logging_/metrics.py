"""Edit accuracy and latency breakdown helpers."""

from src.state import AgentState


def get_edit_accuracy(state: AgentState) -> tuple[int, int]:
    """Return (edit_attempts, edit_applied)."""
    return (state.get("edit_attempts") or 0, state.get("edit_applied") or 0)


def format_latency_breakdown(state: AgentState) -> str:
    """Format latency_breakdown for logging."""
    lb = state.get("latency_breakdown") or {}
    parts = [f"{k}={v}ms" for k, v in lb.items()]
    return ", ".join(parts) if parts else "no data"
