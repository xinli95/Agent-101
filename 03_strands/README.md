# Strands Agents

[Strands Agents](https://strandsagents.com) is an open-source SDK from AWS for building production-grade AI agents. It uses Amazon Bedrock as the default LLM provider (Claude by default).

## Examples

| # | Script | Concept |
|---|--------|---------|
| 01 | `01_basic_agent/agent.py` | Creating an agent with the `@tool` decorator |
| 02 | `02_tool_use/agent.py` | Multiple tools and built-in Strands tools |
| 03 | `03_multi_agent/multi_agent.py` | Agent-as-tool: wrapping agents as callable tools |

## Setup

```bash
pip install -e ".[strands]"

# Configure AWS credentials (one of):
aws configure
# or set env vars in .env: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION

# Enable Bedrock model access in your AWS console:
# AWS Console → Bedrock → Model access → Enable Claude models
```

## Key Concepts

- `@tool` — Decorator that turns any Python function into an agent tool. The docstring is the tool description.
- `Agent(tools=[...])` — The main agent class. Handles the tool loop automatically via Bedrock.
- **Agent-as-tool** — Wrap an `Agent` instance in a `@tool` function to let one agent call another.
- No explicit loop needed — Strands manages the ReAct loop internally.
