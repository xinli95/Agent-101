# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Agent-101 is an educational tutorial repo for building AI agents in Python. It starts with the raw agentic loop (Anthropic API, no framework) and progressively covers four frameworks (LangChain, LangGraph, Strands Agents, Google ADK).

## Commands

```bash
# Install by section
pip install -e ".[langchain]"
pip install -e ".[langgraph]"
pip install -e ".[strands]"
pip install -e ".[google-adk]"
pip install -e ".[all]"
pip install -e ".[dev]"   # ruff + pytest

# Run any example
python 01_raw_loop/01_basic_loop/agent.py

# Lint / format
ruff check .
ruff format .

# Tests (once added)
pytest
```

## Structure

```
00_foundations/       — Framework-agnostic markdown docs
01_raw_loop/          — Raw Anthropic API, no framework; 9 progressive sessions
02_langchain/         — LangChain (OpenAI backend)
03_langgraph/         — LangGraph (OpenAI backend)
04_strands/           — Strands Agents (AWS Bedrock / Claude)
05_google_adk/        — Google ADK (Gemini)
patterns/             — Cross-framework comparisons (same task, 4 implementations)
  react/              ✅ complete
  plan_and_execute/   🚧 stubs
  reflection/         🚧 stubs
  multi_agent/        🚧 stubs
```

## LLM Backends

- `01_raw_loop/`: Anthropic API directly (`claude-opus-4-6`)
- `02_langchain/`, `03_langgraph/`: OpenAI (`gpt-4o-mini`)
- `04_strands/`: Amazon Bedrock (Claude, via AWS credentials)
- `05_google_adk/`: Gemini (`gemini-2.0-flash`)

## Architecture Notes

**Raw loop sessions (01_raw_loop/):** Each session adds one mechanism without changing the core loop. Sessions 01–04 are complete implementations; 05–09 are documented stubs.

**Google ADK** is async-first — all scripts use `asyncio.run(main())`. ADK tools must return `dict`.

**Strands** tools are plain Python functions decorated with `@tool`; return values can be any type.

**Tool docstrings** are the tool descriptions the LLM reads — write them for the model, not the developer.

## Adding New Content

- Follow the numbering within each section (`05_`, `06_`, etc.)
- For `patterns/`: implement the same task across all 4 frameworks for direct comparison
- Raw loop sessions should each add **one mechanism only** — don't combine multiple concepts
