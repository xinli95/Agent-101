# LangChain

LangChain is the most widely-used agent framework. It's the best starting point if you're new to agents.

## Examples

| # | Script | Concept |
|---|--------|---------|
| 01 | `01_react_agent/agent.py` | ReAct pattern with `create_react_agent` + `AgentExecutor` |
| 02 | `02_tool_calling/agent.py` | Direct tool calling via `bind_tools()` — no ReAct prompting |
| 03 | `03_memory/agent.py` | Conversation memory: buffer and summary |
| 04 | `04_rag_agent/agent.py` | RAG as an agent tool (retriever → tool) |

## Setup

```bash
pip install -e ".[langchain]"
cp .env.example .env  # add OPENAI_API_KEY
```

## Run

```bash
python 01_langchain/01_react_agent/agent.py
```

## Key Concepts

- `@tool` — Decorator to define a tool from a Python function. The docstring becomes the tool description.
- `create_react_agent` — Builds a ReAct agent from an LLM, tools, and a prompt template.
- `AgentExecutor` — Runs the agent loop (calls LLM → calls tools → calls LLM → ...).
- `bind_tools()` — Attaches tools to the LLM for native function calling (bypasses ReAct prompting).
