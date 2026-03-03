# Agent-101

**Deep Dive into Agents** — A practical, framework-by-framework guide to building AI agents in Python.

## What You'll Learn

- Core agent concepts: the agent loop, tool use, memory, and planning
- How to implement the same patterns across 4 major frameworks
- When to use each framework and why

## Frameworks Covered

| Framework | LLM Backend | Best For |
|-----------|-------------|----------|
| [LangChain](01_langchain/) | OpenAI | Getting started quickly |
| [LangGraph](02_langgraph/) | OpenAI | Complex, stateful, graph-based flows |
| [Strands Agents](03_strands/) | AWS Bedrock (Claude) | Production AWS workloads |
| [Google ADK](04_google_adk/) | Gemini | Google Cloud workloads |

## Learning Path

1. **[00_foundations/](00_foundations/)** — Read this first. Framework-agnostic concepts.
2. **[01_langchain/](01_langchain/)** — Start here if you're new to agents.
3. **[02_langgraph/](02_langgraph/)** — Go deeper with graph-based orchestration.
4. **[03_strands/](03_strands/)** or **[04_google_adk/](04_google_adk/)** — Explore cloud-native options.
5. **[patterns/](patterns/)** — See the same pattern implemented across all 4 frameworks.

## Setup

```bash
git clone https://github.com/xinli95/Agent-101.git
cd Agent-101

cp .env.example .env
# Edit .env with your API keys

# Install a specific framework
pip install -e ".[langchain]"
pip install -e ".[langgraph]"
pip install -e ".[strands]"
pip install -e ".[google-adk]"

# Or install everything
pip install -e ".[all]"
```

Run any example:

```bash
python 01_langchain/01_react_agent/agent.py
```

## Prerequisites

- Python 3.11+
- API keys for the framework(s) you want to use (see `.env.example`)
