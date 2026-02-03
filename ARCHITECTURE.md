# Architecture

This document describes the architecture, data flow, and design decisions of the Coding Agent PoC. It also highlights areas intentionally left simple that could be extended in future iterations.

## Overview

The system implements a **Plan → Act → Observe** agentic loop using LangGraph. The agent receives a user request, plans how to accomplish it, executes tools, verifies the results, and either loops back for corrections or completes.

```
┌──────────────────────────────────────────────────────────────────┐
│                        LangGraph State Machine                    │
│                                                                   │
│   START → Router → Context Engine → Plan ←→ Tools                │
│                                       ↓                          │
│                                    Verify                         │
│                                       ↓                          │
│                                   Observe → END (or loop back)   │
└──────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. State (`src/state.py`)

The `AgentState` TypedDict defines all data flowing through the graph:

| Field | Type | Purpose |
|-------|------|---------|
| `messages` | `list` | Conversation history (uses `add_messages` reducer) |
| `user_request` | `str` | Original user request |
| `workspace_path` | `str` | Directory the agent operates on |
| `loop_count` | `int` | Number of Plan→Observe cycles completed |
| `model_tier` | `"high" \| "fast"` | Selected model tier |
| `current_phase` | `str` | Current execution phase |
| `context_snippets` | `list[str]` | Retrieved code snippets |
| `verification_result` | `dict` | Test execution results |
| `trajectory` | `list[dict]` | Action history (uses `add` reducer) |
| `edit_attempts` | `int` | Total file edit attempts |
| `edit_applied` | `int` | Successfully applied edits |
| `latency_breakdown` | `dict` | Timing metrics |

**Extension opportunity**: Add fields for caching, memory across sessions, or more granular metrics.

---

### 2. Router (`src/router.py`)

**Purpose**: Select the appropriate model tier based on request complexity.

**Current implementation**: Simple heuristic—uses "high" tier if the request contains "complex" or is longer than 100 characters.

```python
if "complex" in request.lower() or len(request) > 100:
    model_tier = "high"  # gemini-2.5-pro / gpt-4o
else:
    model_tier = "fast"  # gemini-2.5-flash / gpt-4o-mini
```

**Extension opportunities**:
- Use an LLM to classify request complexity
- Implement task-specific routing (code generation vs. debugging vs. refactoring)
- Add cost-aware routing based on token estimates
- Route based on language/framework detection

---

### 3. Context Engine (`src/context_engine.py`)

**Purpose**: Retrieve relevant code snippets from the workspace to provide context to the LLM.

**Current implementation**: Simple keyword matching—extracts words from the user request and scores files by keyword frequency.

```python
keywords = [w.lower() for w in user_request.split() if len(w) > 2][:10]
# Score files by keyword matches, return top snippets up to 8KB
```

**Extension opportunities**:
- Implement semantic search with embeddings (e.g., using ChromaDB or FAISS)
- Add AST-based code understanding for better snippet extraction
- Implement repository mapping (file dependencies, call graphs)
- Use tree-sitter for language-aware parsing
- Add caching for repeated queries

---

### 4. Orchestrator (`src/orchestrator.py`)

**Purpose**: Build and compile the LangGraph state machine that coordinates all nodes.

**Nodes**:

| Node | Function | Description |
|------|----------|-------------|
| `router` | `router_node` | Selects model tier |
| `context_engine` | `context_engine_node` | Retrieves context snippets |
| `plan` | `build_plan_node()` | LLM generates tool calls |
| `tools` | `build_tools_node()` | Executes tool calls |
| `verify` | `build_verify_node()` | Runs tests |
| `observe` | `build_observe_node()` | Decides to continue or end |

**Edges and routing**:

```
START → router → context_engine → plan
plan → tools (if tool_calls exist)
plan → verify (if no tool_calls)
tools → plan (loop back for more planning)
verify → observe
observe → plan (if not done and under MAX_LOOPS)
observe → END (if done or MAX_LOOPS reached)
```

**Key behaviors**:
- Retries if no action was taken on first loop
- Tracks edit attempts vs. applied for accuracy metrics
- Accumulates latency breakdown for model and sandbox time

**Extension opportunities**:
- Add checkpointing for pause/resume
- Implement parallel tool execution
- Add human-in-the-loop approval gates at plan stage
- Implement rollback on verification failure

---

### 5. Tool Harness (`src/tool_harness.py`)

**Purpose**: Bind tools to the workspace and create the LangGraph ToolNode.

**Design**: Tools are defined with a `workspace_root` parameter, but the harness wraps them to always inject the correct workspace path. This keeps tool definitions clean while ensuring workspace isolation.

```python
def _bind_workspace(tool, workspace):
    def invoker(**kwargs):
        kwargs["workspace_root"] = workspace
        return tool.invoke(kwargs)
    return StructuredTool.from_function(...)
```

**Available tools**:
- `grep_tool` - Search file contents
- `read_file_tool` - Read file contents
- `search_replace_tool` - Edit files with diff preview
- `write_file_tool` - Create/overwrite files with diff preview
- `run_shell_tool` - Execute shell commands

**Extension opportunities**:
- Add more tools (git operations, web search, API calls)
- Implement tool-specific rate limiting
- Add tool result caching
- Implement tool composition (macros)

---

### 6. Tools (`src/tools/`)

#### 6.1 Read File (`read_file.py`)
Simple file reading with path validation and encoding handling.

#### 6.2 Write File (`write_file.py`)
Creates or overwrites files. **Includes human-in-the-loop confirmation** with diff preview for existing files or content preview for new files.

#### 6.3 Search Replace (`search_replace.py`)
Performs exact string replacement in files. **Includes human-in-the-loop confirmation** with colorized diff preview.

#### 6.4 Diff Utils (`diff_utils.py`)
Utility module for generating human-readable diffs:
- `generate_diff()` - Creates unified diff with colors
- `generate_new_file_preview()` - Shows new file contents
- `ask_user_confirmation()` - Prompts user with diff and Y/n confirmation

#### 6.5 Grep (`grep.py`)
Searches for patterns in files using Python's pathlib and string matching.

**Extension opportunity**: Use ripgrep subprocess for better performance on large codebases.

#### 6.6 Shell (`shell.py`)
Runs arbitrary shell commands in the workspace.

**Extension opportunities**:
- Add command allowlisting/denylisting
- Implement sandboxing (Docker, nsjail)
- Add output streaming for long-running commands

---

### 7. Sandbox (`src/sandbox.py`)

**Purpose**: Execute shell commands with timeout and error handling.

**Current implementation**: Uses `subprocess.run()` with configurable timeout and captures stdout/stderr.

```python
result = subprocess.run(
    command,
    shell=True,
    cwd=cwd,
    capture_output=True,
    timeout=timeout_seconds,
)
```

**Extension opportunities**:
- Implement Docker-based isolation
- Add resource limits (CPU, memory)
- Implement network isolation
- Add command logging and audit trail

---

### 8. Logging (`src/logging_/`)

#### 8.1 Visual (`visual.py`)
Rich console output for real-time feedback:
- `log_state_transition()` - Shows current node/phase/loop
- `print_trajectory_table()` - Displays action history
- `print_summary()` - Final metrics summary

#### 8.2 Trajectory (`trajectory.py`)
Appends action entries to the state trajectory list.

**Extension opportunities**:
- Add persistent logging to files/database
- Implement OpenTelemetry tracing
- Add LangSmith integration for debugging

---

## Data Flow

### Successful Edit Flow

```
1. User: "Add logging to main.py"
2. Router: model_tier = "fast"
3. Context Engine: retrieves main.py snippet
4. Plan: LLM decides to call read_file("main.py")
5. Tools: reads main.py, returns content
6. Plan: LLM decides to call search_replace(old="def main", new="def main\n    logging.info...")
7. Tools:
   a. Generates colorized diff
   b. Shows diff to user
   c. User confirms (Y)
   d. Applies change
   e. Returns "applied: patch written successfully"
8. Plan: LLM sees success, no more tool calls
9. Verify: runs pytest (passes)
10. Observe: passed=True, ends loop
11. Summary: edit_attempts=1, edit_applied=1, accuracy=100%
```

### Rejected Edit Flow

```
1-6. Same as above
7. Tools:
   a. Generates colorized diff
   b. Shows diff to user
   c. User declines (n)
   d. Returns "rejected: user declined the changes"
8. Plan: LLM sees rejection, may try alternative approach
9. Continue loop...
```

---

## Configuration

### Model Selection

The orchestrator selects models based on tier:

| Tier | Google Gemini | OpenAI |
|------|--------------|--------|
| high | gemini-2.5-pro | gpt-4o |
| fast | gemini-2.5-flash | gpt-4o-mini |

### Constants

| Constant | Value | Location |
|----------|-------|----------|
| `MAX_LOOPS` | 10 | orchestrator.py |
| `VERIFY_COMMAND` | `pytest --tb=short -q` | orchestrator.py |
| `max_chars` (context) | 8000 | context_engine.py |

---

## Future Extensions

### High Priority
1. **Semantic search**: Replace keyword matching with embeddings for better context retrieval
2. **Better sandboxing**: Docker-based isolation for shell commands
3. **Git integration**: Tools for commit, diff, branch operations
4. **Streaming output**: Show LLM responses as they generate

### Medium Priority
5. **Checkpointing**: Save/restore state for long-running tasks
6. **Multi-file edits**: Batch multiple changes with single confirmation
7. **Undo/rollback**: Revert changes on failure
8. **Persistent memory**: Remember context across sessions

### Nice to Have
9. **Web UI**: Browser-based interface
10. **Plugin system**: User-defined tools
11. **Cost tracking**: Token usage and API cost estimates
12. **Test generation**: Automatically generate tests for changes

---

## Design Decisions

### Why LangGraph?
- First-class support for cycles (Plan → Tools → Plan)
- Built-in state management with reducers
- Clean separation of nodes and edges
- Easy to add checkpointing and persistence

### Why human-in-the-loop for edits?
- Prevents unintended changes to codebases
- Builds user trust in the agent
- Allows users to catch mistakes before they happen
- Can be disabled in future for trusted workflows

### Why simple keyword matching for context?
- Zero external dependencies
- Fast enough for small codebases
- Easy to understand and debug
- Placeholder for proper semantic search later

### Why subprocess for sandbox?
- Simple and reliable
- Works on all platforms
- Easy to understand failure modes
- Placeholder for proper isolation later
