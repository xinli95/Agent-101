# Agent-101

**Deep Dive into Agents** — Build agents with major frameworks, then see how Claude Code works under the hood.

## Structure

```
00_foundations/   — Core concepts: agent loop, tool use, memory, design patterns
01_langchain/     — LangChain: the most widely-used agent framework
02_langgraph/     — LangGraph: graph-based, stateful orchestration
03_strands/       — Strands Agents: AWS-native (Amazon Bedrock)
04_google_adk/    — Google ADK: Gemini-native (Google Cloud)
patterns/         — Same problem implemented in all frameworks side-by-side
06_claude_code/   — How Claude Code works: build it from scratch, session by session
```

## Learning Path

1. **[00_foundations/](00_foundations/)** — Read this first. The "why" before the "how."
2. **[01_langchain/](01_langchain/)** — Start here for framework-based agents.
3. **[02_langgraph/](02_langgraph/)** — Go deeper: explicit graph control.
4. **[03_strands/](03_strands/)** / **[04_google_adk/](04_google_adk/)** — Cloud-native options.
5. **[patterns/](patterns/)** — Compare all 4 frameworks on the same task.
6. **[06_claude_code/](06_claude_code/)** — Go under the hood: rebuild Claude Code's agentic loop from scratch using the Anthropic API directly.

## Frameworks & LLM Backends

| Section | Framework | LLM |
|---------|-----------|-----|
| `01_langchain/` | LangChain | OpenAI `gpt-4o-mini` |
| `02_langgraph/` | LangGraph | OpenAI `gpt-4o-mini` |
| `03_strands/` | Strands Agents | AWS Bedrock (Claude) |
| `04_google_adk/` | Google ADK | Gemini `gemini-2.0-flash` |
| `06_claude_code/` | Anthropic SDK (no framework) | Claude (direct API) |

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
python 01_langchain/01_react_agent/agent.py
python 06_claude_code/01_basic_loop/agent.py
```

## Prerequisites

- Python 3.11+
- API keys as needed (see `.env.example`)
