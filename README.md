# Coding Agent PoC

A proof-of-concept **agentic coding loop** (Plan → Act → Observe) built with [LangGraph](https://langchain-ai.github.io/langgraph/) > 1.0. It implements the architecture described in [SPECS.md](SPECS.md): Router, Context Engine, Tool Harness, and Sandbox, with mock tools that operate on a local workspace folder.

## How it works

1. **User** sends a request (e.g. “Fix the bug in the login auth flow”).
2. **Router** chooses model tier (high-reasoning vs fast) from the request.
3. **Context Engine** retrieves relevant snippets from the workspace (keyword match).
4. **Plan** node: the LLM decides what to do and calls tools (grep, search_replace, run_shell).
5. **Tools** run in the workspace (search, edit files, run commands).
6. **Verify** runs tests in the sandbox (e.g. `pytest`).
7. **Observe** checks the result and either loops back to Plan or ends.

Flow: **User → Router → Context Engine → Plan → (Tools → Plan)* → Verify → Observe → (Plan or END)**.

### Files

| File | Role |
|------|------|
| [src/state.py](src/state.py) | Graph state schema and reducers |
| [src/orchestrator.py](src/orchestrator.py) | Builds and compiles the LangGraph (Plan, Tools, Verify, Observe) |
| [src/router.py](src/router.py) | Mock router: model selection |
| [src/context_engine.py](src/context_engine.py) | Mock retrieval from workspace |
| [src/tool_harness.py](src/tool_harness.py) | Tools + ToolNode bound to workspace |
| [src/sandbox.py](src/sandbox.py) | Runs shell commands in workspace |
| [src/tools/](src/tools/) | Mock tools: grep, search_replace, run_shell |
| [src/logging_/](src/logging_/) | Trajectory, metrics, Rich visual logging |

Mock tools operate under `workspace_path` (a folder in the project, default `./workspace`).

## Setup

### 1. Environment (uv)

- Create a virtualenv and install dependencies with [uv](https://docs.astral.sh/uv/):

  ```bash
  uv venv
  uv sync
  ```

- Run the app with:

  ```bash
  uv run main.py "Your request here"
  ```

  This uses the project’s `.venv` automatically.

### 2. API keys

- Copy the example env file and set at least one LLM key:

  ```bash
  cp env.example .env
  ```

- Edit `.env` and set:

  - `GOOGLE_API_KEY=` — for Google Gemini (used by default).
  - `OPENAI_API_KEY=` — optional fallback if Gemini is not set.

The app loads `.env` via `python-dotenv` at startup.

## Usage

```bash
# Default request, workspace ./workspace
uv run main.py

# Custom request and workspace
uv run main.py "Add a docstring to every function in the codebase" --workspace ./my_code

# Limit graph steps
uv run main.py "Run tests" --recursion-limit 10
```

## Logging and observability

- **State transitions**: each node logs current phase and loop count (Rich panels).
- **Trajectory**: sequence of actions (plan, verify, observe) is stored in state and printed at the end.
- **Summary**: edit attempts/applied, latency breakdown (model_ms, sandbox_ms), loop count, trajectory length.

These appear in the console during the run and in the final summary table.
