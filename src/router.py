"""Router node: mock model selection (high-reasoning vs fast)."""

from src.state import AgentState


def router_node(state: AgentState) -> dict:
    """Decide model tier from user request. Log and return state update."""
    request = (state.get("user_request") or "").strip()
    if "complex" in request.lower() or len(request) > 100:
        model_tier = "high"
    else:
        model_tier = "fast"
    return {
        "model_tier": model_tier,
        "current_phase": "retrieve",
    }
