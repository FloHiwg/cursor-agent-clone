# Coding Agent PoC

A proof-of-concept **agentic coding loop** (Plan → Act → Observe) built with [LangGraph](https://langchain-ai.github.io/langgraph/). This implements a minimal but functional AI coding assistant that can read, write, and modify files in a workspace while asking for user confirmation before making changes.

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Features

- **Agentic Loop**: Plan → Act → Observe cycle with automatic retries
- **Human-in-the-Loop**: Shows colorized diffs and asks for user confirmation before applying changes
- **Multiple LLM Support**: Works with Google Gemini (default) or OpenAI GPT-4
- **Tool Suite**: grep, read/write files, search-replace, shell commands
- **Observability**: Rich console output with state transitions, trajectory tracking, and run summaries

## Quick Start

### 1. Install dependencies

```bash
uv venv
uv sync
```

### 2. Configure API keys

```bash
cp env.example .env
# Edit .env and set GOOGLE_API_KEY or OPENAI_API_KEY
```

### 3. Run the agent

```bash
uv run main.py "Create a hello world Python script"
```

The agent will show you a diff of proposed changes and ask for confirmation before writing files.

## Usage Examples

```bash
# Create a new file
uv run main.py "Create a FastAPI endpoint that returns a greeting"

# Modify existing code
uv run main.py "Add error handling to the main function" --workspace ./my_project

# Run with custom recursion limit
uv run main.py "Refactor the database module" --recursion-limit 15
```

## How It Works

```
User Request
     ↓
┌─────────┐
│ Router  │ → Selects model tier (high/fast)
└────┬────┘
     ↓
┌─────────────────┐
│ Context Engine  │ → Retrieves relevant code snippets
└────────┬────────┘
     ↓
┌─────────┐     ┌─────────┐
│  Plan   │ ←→  │  Tools  │ → Executes with user confirmation
└────┬────┘     └─────────┘
     ↓
┌─────────┐
│ Verify  │ → Runs tests (pytest)
└────┬────┘
     ↓
┌─────────┐
│ Observe │ → Continue or finish
└────┬────┘
     ↓
  Result
```

## Project Structure

```
├── main.py                 # CLI entry point
├── src/
│   ├── orchestrator.py     # LangGraph state machine
│   ├── state.py            # State schema (TypedDict)
│   ├── router.py           # Model tier selection
│   ├── context_engine.py   # Code snippet retrieval
│   ├── tool_harness.py     # Tool binding and ToolNode
│   ├── sandbox.py          # Shell command execution
│   ├── tools/
│   │   ├── read_file.py    # Read file contents
│   │   ├── write_file.py   # Write files (with diff preview)
│   │   ├── search_replace.py # Edit files (with diff preview)
│   │   ├── grep.py         # Search file contents
│   │   ├── shell.py        # Run shell commands
│   │   └── diff_utils.py   # Diff generation and user confirmation
│   └── logging_/
│       ├── visual.py       # Rich console output
│       └── trajectory.py   # Action sequence tracking
└── workspace/              # Default working directory
```

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `GOOGLE_API_KEY` | Google Gemini API key (preferred) |
| `OPENAI_API_KEY` | OpenAI API key (fallback) |

## Observability

The agent provides real-time feedback:

- **State panels**: Shows current node, phase, and loop count
- **Diff previews**: Colorized unified diffs before file changes
- **Trajectory table**: Sequence of actions taken
- **Run summary**: Edit accuracy, latency breakdown, total loops

## License

MIT
