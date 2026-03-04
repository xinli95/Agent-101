# Agent-101

**Deep Dive into Agents** — Build agents from the ground up, then see how frameworks abstract the same patterns.

## Structure

```
00_foundations/   — Core concepts: agent loop, tool use, memory, design patterns
01_raw_loop/      — Build a Claude Code-style agent from scratch (Anthropic API only)
02_langchain/     — LangChain: the most widely-used agent framework
03_langgraph/     — LangGraph: graph-based, stateful orchestration
04_strands/       — Strands Agents: AWS-native (Amazon Bedrock)
05_google_adk/    — Google ADK: Gemini-native (Google Cloud)
patterns/         — Same problem implemented in all frameworks side-by-side
```

## Learning Path

1. **[00_foundations/](00_foundations/)** — Read this first. The "why" before the "how."
2. **[01_raw_loop/](01_raw_loop/)** — Build the loop yourself. 9 sessions, one new mechanism each.
3. **[02_langchain/](02_langchain/)** — Start here for framework-based agents.
4. **[03_langgraph/](03_langgraph/)** — Go deeper: explicit graph control.
5. **[04_strands/](04_strands/)** / **[05_google_adk/](05_google_adk/)** — Cloud-native options.
6. **[patterns/](patterns/)** — Compare all 4 frameworks on the same task.

The raw loop section answers: *"what is LangGraph actually doing?"* The framework sections answer: *"how do I use it productively?"*

## Frameworks & LLM Backends

| Section | Framework | LLM |
|---------|-----------|-----|
| `01_raw_loop/` | Anthropic SDK (no framework) | Claude (direct API) |
| `02_langchain/` | LangChain | OpenAI `gpt-4o-mini` |
| `03_langgraph/` | LangGraph | OpenAI `gpt-4o-mini` |
| `04_strands/` | Strands Agents | AWS Bedrock (Claude) |
| `05_google_adk/` | Google ADK | Gemini `gemini-2.0-flash` |

## Setup

```bash
git clone https://github.com/xinli95/Agent-101.git
cd Agent-101

cp .env.example .env
# Edit .env — add keys for the sections you want to run

# Install by section
pip install -e ".[langchain]"
pip install -e ".[langgraph]"
pip install -e ".[strands]"
pip install -e ".[google-adk]"
pip install -e ".[all]"         # everything
```

Run any example:

```bash
python 01_raw_loop/01_basic_loop/agent.py
python 02_langchain/01_react_agent/agent.py
```

## Prerequisites

- Python 3.11+
- API keys as needed (see `.env.example`)
