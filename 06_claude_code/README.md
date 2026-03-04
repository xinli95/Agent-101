# How Claude Code Works

Build a Claude Code-style agent from scratch using the Anthropic API directly — no frameworks.

Each session adds **one mechanism** without changing the core loop. By the end you'll understand exactly what's happening inside Claude Code (and what LangGraph, Strands, and ADK are abstracting).

## The Core Insight

The entire foundation fits in five lines:

```python
while response.stop_reason == "tool_use":
    results = [run_tool(block) for block in response.content if block.type == "tool_use"]
    messages.append({"role": "user", "content": results})
    response = client.messages.create(messages=messages, tools=TOOLS, ...)
```

That's it. Every agent framework in this repo is a more ergonomic wrapper around this loop.

## Sessions

| # | Script | Adds |
|---|--------|------|
| 01 | `01_basic_loop/agent.py` | The `while stop_reason == "tool_use"` loop + one bash tool |
| 02 | `02_tool_use/agent.py` | Multiple tools: bash, read, write, edit |
| 03 | `03_planning/agent.py` | TodoWrite: structured task decomposition |
| 04 | `04_subagents/agent.py` | Spawning sub-agents with isolated context |
| 05 | `05_skills/agent.py` | Loading skill files into the system prompt |
| 06 | `06_context_mgmt/agent.py` | Summarizing old messages to free context |
| 07 | `07_task_system/agent.py` | File-based task CRUD with dependency graph |
| 08 | `08_background/agent.py` | Daemon threads + completion notifications |
| 09 | `09_agent_teams/agent.py` | Multiple agents communicating via mailboxes |

## Setup

Sessions 01–04 are complete, working implementations. Sessions 05–09 are documented stubs with implementation guides.

## Setup

```bash
pip install anthropic python-dotenv
# Add ANTHROPIC_API_KEY to .env
python 06_claude_code/01_basic_loop/agent.py
```
