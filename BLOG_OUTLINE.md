# Blog Article Outline: Building a Coding Agent PoC

> **Angle:** From ByteByteGo’s spec to a working Plan → Act → Observe loop in Python with LangGraph.

---

## 1. The Idea Behind the Project

- **Beyond chat:** Most “AI coding” UIs are chat + copy-paste. The goal here is an **agentic loop** that searches, edits, and verifies code inside a real workspace.
- **Inspiration:** Spec and concept adapted from a ByteByteGo article on coding agent architecture (cite/link when you publish).
- **Core thesis:** Reliability comes from **tools** (grep, search-replace, shell), not from the model generating raw diffs. Solving the “diff problem” by making the model call structured tools instead of outputting free-form patches.
- **What we built:** A PoC that implements Brain (orchestrator + model) and Body (tool harness + sandbox), with a ReAct-style loop: Plan → Act → Observe, including verification and iteration.

---

## 2. The Spec in a Nutshell

- **Architecture (from SPECS):**
  - **Orchestrator:** State machine and control loop (Plan → Act → Observe).
  - **Router:** Chooses high-reasoning vs fast model from the request.
  - **Context Engine:** Pulls relevant snippets into the prompt to avoid context overflow.
  - **Tool Harness:** Interface for the model to use filesystem/terminal (grep, read, search-replace, write, shell).
  - **Sandbox:** Isolated execution for verification (here: subprocess in workspace; spec allows Docker/VM).

- **Core tools (the “hands”):**
  - Search/grep for navigation.
  - Search & replace for **mechanical** edits (exact `old_string` → `new_string`).
  - Terminal/shell for builds and tests.

- **Execution loop (ReAct-style):**
  1. Input: user request (e.g. “Fix the bug in the login flow”).
  2. Plan: model decides what to search/edit.
  3. Retrieve: context engine adds relevant snippets.
  4. Edit: model issues search-replace (and other tool) calls.
  5. Verify: run tests in the sandbox (e.g. `pytest`).
  6. Iterate: on failure, feed errors back and loop to Plan.

- **Spec takeaways:** Context compaction, optional speculative execution, fast sandboxing; logging trajectory, edit accuracy (attempted vs applied), and latency breakdown for observability and trust.

---

## 3. Walking Through the Code

### 3.1 Entry point and state

- **`main.py`:** CLI with `request`, `--workspace`, `--recursion-limit`. Loads env, builds the graph, sets initial state (user_request, workspace_path, messages, loop_count, current_phase, context_snippets, verification_result, trajectory, edit_attempts/edit_applied, latency_breakdown). Invokes graph and prints summary + trajectory table.
- **`src/state.py`:** `AgentState` TypedDict: messages (with `add_messages`), user_request, workspace_path, loop_count, model_tier, current_phase, context_snippets, verification_result, trajectory, edit_attempts, edit_applied, latency_breakdown. This is the single source of truth for the graph.

### 3.2 The graph: orchestrator

- **`src/orchestrator.py`:** Builds the LangGraph.
  - **Nodes:** router → context_engine → plan → (tools | verify) → observe → plan or END.
  - **Router:** Sets `model_tier` (e.g. “complex” or long request → high, else fast).
  - **Context engine:** Fetches snippets (see below).
  - **Plan:** Binds tools to the LLM, injects system prompt (workspace file list, “use tools; read_file then search_replace”), runs LLM; on tool_calls → tools, else → verify.
  - **Tools:** ToolNode runs the actual tools; orchestrator wraps it to count edit_attempts / edit_applied from tool results.
  - **Verify:** Runs a fixed command (e.g. `pytest`) in the sandbox, stores result and sandbox latency.
  - **Observe:** Increments loop_count; if tests passed or MAX_LOOPS reached → END, else → plan.
- **Conditional edges:** `route_after_plan` (tools vs verify), `route_after_observe` (plan vs END).

### 3.3 Context engine

- **`src/context_engine.py`:** Simple retrieval: keyword extraction from `user_request`, score files (e.g. `.py`, `.md`, `.txt`) by keyword matches, return top snippets up to a character budget. Shows the idea of “retrieve then inject” without a full RAG stack.

### 3.4 Tool harness and tools

- **`src/tool_harness.py`:** Builds the list of tools with `workspace_root` bound so the graph always passes the same workspace. Uses LangGraph’s `ToolNode` to execute tool calls from the plan node.
- **Tools (examples to highlight):**
  - **`grep_tool`:** Pattern + path (relative to workspace); returns `file:line: content` lines. Example: “find all uses of `divide`” → grep in workspace.
  - **`search_replace_tool`:** `file_path`, `old_string`, `new_string` (exact match). Emphasize: model must call `read_file` first to get exact text; then one replace. Return strings like “applied: patch written successfully” or “attempted: old_string not found” for logging.
  - **`read_file` / `write_file`:** Read or overwrite file in workspace.
  - **`run_shell_tool`:** Run a command in workspace (e.g. run tests or scripts).

### 3.5 Sandbox

- **`src/sandbox.py`:** `run_command(command, cwd, timeout)`: subprocess in `cwd`, returns `{ passed, output, duration_ms }`. PoC uses local process; spec allows Docker/VM for real isolation.

### 3.6 Router

- **`src/router.py`:** Simple rule: e.g. “complex” in request or length > 100 → high-reasoning model; else fast. Feeds `model_tier` into the plan node for LLM selection (e.g. Gemini Pro vs Flash, or GPT-4o vs mini).

---

## 4. Concrete Examples to Include

- **Example 1 – List files:** Request: “List all Python files in the workspace.” Flow: router (fast) → context_engine → plan → model calls `grep_tool` or equivalent; tools return; then verify (pytest) → observe → END. Show a minimal trajectory (plan → tools → verify → observe).
- **Example 2 – Edit and verify:** Request: “Add a docstring to the `add` function in calculator.py.” Flow: plan → read_file(calculator.py) → search_replace with exact `old_string` (the current `def add(...)`) and `new_string` (with docstring). Then verify runs pytest; if green, observe → END. Optionally show one “attempted vs applied” case (e.g. whitespace mismatch) to illustrate why exact-match search-replace and read_file-first matter.
- **Example 3 – Loop on failure:** Request: “Make the calculator handle division by zero.” First edit might be wrong; verify fails; observe loops back to plan; model sees test output and issues a new search_replace; second loop passes. Good place to show trajectory table (plan → tools → verify → observe → plan → tools → verify → observe → END).

---

## 5. Logging and Observability (from spec)

- **Trajectory:** Each node appends (phase, action, detail) to state; printed at end (e.g. last N steps) so readers see the exact sequence.
- **Edit accuracy:** Counts of edit_attempts vs edit_applied; if a patch fails (old_string not found), it’s visible for tuning prompts or tooling.
- **Latency breakdown:** model_ms (plan node), sandbox_ms (verify). Mention that spec also suggests tracking tool execution time for bottleneck analysis.

---

## 6. Wrap-up

- **What we learned:** Tool-first design (search-replace over raw diffs) and a clear Plan → Act → Observe loop make the agent predictable and debuggable. ByteByteGo’s spec maps neatly onto LangGraph nodes and state.
- **Possible next steps:** Real RAG or embeddings in context_engine; Docker sandbox; speculative execution for boilerplate; more tools (e.g. apply patch from diff). Link to repo and SPECS.md.

---

## Checklist for drafting

- [ ] Add ByteByteGo article link when available.
- [ ] Insert 1–2 short code snippets (e.g. `build_graph`, one tool signature, one route function).
- [ ] Add a simple flow diagram (Router → Context → Plan → Tools/Verify → Observe → Plan/END) if the blog supports images.
- [ ] Keep code walk in “outline” form so the final post can expand each bullet into a paragraph or two.
