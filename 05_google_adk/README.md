# Google ADK

[Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) is Google's open-source Python framework for building agents on Gemini models. It integrates natively with Google Cloud and Vertex AI.

## Examples

| # | Script | Concept |
|---|--------|---------|
| 01 | `01_basic_agent/agent.py` | Defining an Agent with FunctionTool, Runner, and sessions |
| 02 | `02_tool_use/agent.py` | Multiple tools including Google's built-in Search and code execution |
| 03 | `03_multi_agent/multi_agent.py` | Sub-agents via AgentTool for hierarchical delegation |

## Setup

```bash
pip install -e ".[google-adk]"

# Option 1: API key
echo "GOOGLE_API_KEY=your-key" >> .env

# Option 2: Application Default Credentials (for GCP)
gcloud auth application-default login
```

## Key Concepts

- `Agent` — The core class. Requires `name`, `model`, `instruction`, and optionally `tools`.
- `FunctionTool` — Wraps a plain Python function as a tool. The function's docstring and type hints define the schema.
- `Runner` — Executes the agent against a session and streams events.
- `InMemorySessionService` — Manages conversation sessions in memory.
- `AgentTool` — Wraps an `Agent` as a tool so a parent agent can delegate to it.
- ADK uses `async`/`await` throughout — all examples use `asyncio.run()`.
