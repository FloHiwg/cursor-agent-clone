"""Trajectory trace: append action sequence entries to state."""

import time
from typing import Any


def append_trajectory(phase: str, action: str, detail: str = "") -> dict[str, Any]:
    """Return a state update that appends one trajectory entry (use with reducer)."""
    return {
        "trajectory": [{
            "phase": phase,
            "action": action,
            "detail": detail[:200] if detail else "",
            "timestamp": time.time(),
        }]
    }
