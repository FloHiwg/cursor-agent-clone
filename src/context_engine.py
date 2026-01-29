"""Context engine node: mock retrieval of relevant snippets from workspace."""

from pathlib import Path

from src.state import AgentState


def context_engine_node(state: AgentState) -> dict:
    """Retrieve top-k snippets from workspace by simple keyword match against user_request."""
    workspace_path = state.get("workspace_path") or "."
    user_request = (state.get("user_request") or "").strip()
    root = Path(workspace_path).resolve()
    if not root.is_dir():
        return {"context_snippets": [], "current_phase": "plan"}
    keywords = [w.lower() for w in user_request.split() if len(w) > 2][:10]
    snippets: list[str] = []
    total_chars = 0
    max_chars = 8000
    scored: list[tuple[int, str, str]] = []
    for ext in ("*.py", "*.md", "*.txt"):
        for f in root.rglob(ext):
            if not f.is_file():
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            score = sum(1 for k in keywords if k in text.lower())
            if score > 0:
                rel = f.relative_to(root)
                excerpt = text[:500].replace("\n", " ")
                scored.append((score, str(rel), excerpt))
    scored.sort(key=lambda x: -x[0])
    for _, rel, excerpt in scored:
        if total_chars + len(excerpt) > max_chars:
            break
        snippets.append(f"[{rel}]\n{excerpt}")
        total_chars += len(excerpt)
    return {
        "context_snippets": snippets[:15],
        "current_phase": "plan",
    }
