"""Rich console: state transitions, loop count, summary table."""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.state import AgentState

console = Console()


def log_state_transition(node_name: str, state: AgentState) -> None:
    """Print current node, phase, and loop count."""
    phase = state.get("current_phase", "?")
    loop = state.get("loop_count", 0)
    console.print(
        Panel(
            f"[bold]node[/bold]: {node_name}  [bold]phase[/bold]: {phase}  [bold]loop[/bold]: {loop}",
            title="State",
            border_style="blue",
        )
    )


def print_trajectory_table(trajectory: list[dict[str, Any]], last_n: int = 10) -> None:
    """Print last N trajectory steps as a table."""
    if not trajectory:
        return
    table = Table(title="Trajectory (last steps)")
    table.add_column("Phase", style="cyan")
    table.add_column("Action", style="green")
    table.add_column("Detail", style="dim", max_width=40)
    for entry in trajectory[-last_n:]:
        table.add_row(
            entry.get("phase", ""),
            entry.get("action", ""),
            (entry.get("detail", "") or "")[:40],
        )
    console.print(table)


def print_summary(state: AgentState) -> None:
    """Print edit accuracy, latency breakdown, total steps."""
    table = Table(title="Run Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    attempts, applied = state.get("edit_attempts") or 0, state.get("edit_applied") or 0
    table.add_row("Edit attempts", str(attempts))
    table.add_row("Edit applied", str(applied))
    if attempts > 0:
        table.add_row("Edit accuracy", f"{100 * applied / attempts:.0f}%")
    lb = state.get("latency_breakdown") or {}
    for k, v in lb.items():
        table.add_row(f"Latency {k}", f"{v}ms")
    table.add_row("Loop count", str(state.get("loop_count", 0)))
    table.add_row("Trajectory steps", str(len(state.get("trajectory") or [])))
    console.print(Panel(table, title="Summary", border_style="green"))
