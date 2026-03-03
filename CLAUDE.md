# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Agent-101 is an educational tutorial repo for building AI agents in Python. It covers four frameworks (LangChain, LangGraph, Strands Agents, Google ADK) with working scripts and a cross-framework patterns section.

## Commands

```bash
# Install a specific framework group
pip install -e ".[langchain]"
pip install -e ".[langgraph]"
pip install -e ".[strands]"
pip install -e ".[google-adk]"
pip install -e ".[all]"        # everything
pip install -e ".[dev]"        # ruff + pytest

# Run any example
python 01_langchain/01_react_agent/agent.py

# Lint
ruff check .
ruff format .

# Tests (once added)
pytest
```

## Structure

```
00_foundations/       # Framework-agnostic markdown docs (read first)
01_langchain/         # LangChain examples (OpenAI backend)
02_langgraph/         # LangGraph examples (OpenAI backend)
03_strands/           # Strands Agents examples (AWS Bedrock / Claude)
04_google_adk/        # Google ADK examples (Gemini)
patterns/             # Same problem implemented in all 4 frameworks
  react/              # ✅ Complete — 4 implementations side-by-side
  plan_and_execute/   # 🚧 Stubs
  reflection/         # 🚧 Stubs
  multi_agent/        # 🚧 Stubs
```

## Architecture

Each framework section has a `README.md` covering setup and key concepts. All Python scripts call `load_dotenv()` and read credentials from `.env` (see `.env.example`).

**LLM backends by section:**
- `01_langchain/` and `02_langgraph/`: OpenAI (`gpt-4o-mini`)
- `03_strands/`: Amazon Bedrock (Claude, configured via AWS credentials)
- `04_google_adk/`: Gemini (`gemini-2.0-flash`)

**Google ADK** uses `async`/`await` throughout — all scripts use `asyncio.run(main())`.

**Strands** tool return types are plain Python values; **Google ADK** tools must return `dict`.

## Adding New Examples

- Follow the numbering convention (`05_`, `06_`, etc.) within each framework section.
- Use `@tool` (LangChain/Strands) or `FunctionTool` (Google ADK) for tool definitions.
- The docstring is the tool description — write it for the LLM, not the developer.
- For `patterns/`, implement the same task across all 4 frameworks so they can be compared directly.
