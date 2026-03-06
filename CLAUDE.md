# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Agent-101 is an educational tutorial repo for building AI agents in Python. It covers four major frameworks (LangChain, LangGraph, Strands Agents, Google ADK) plus a deep-dive section that rebuilds Claude Code's agentic loop from scratch using the Anthropic API directly.

## Commands

```bash
# Install by section
pip install -e ".[langchain]"
pip install -e ".[langgraph]"
pip install -e ".[strands]"
pip install -e ".[google-adk]"
pip install -e ".[mcp]"
pip install -e ".[all]"
pip install -e ".[dev]"   # ruff + pytest

# Run any example
python 01_langchain/01_react_agent/agent.py
python 06_claude_code/01_basic_loop/agent.py

# Lint / format
ruff check .
ruff format .
```

## Structure

```
00_foundations/       — Framework-agnostic markdown docs
01_langchain/         — LangChain (OpenAI backend)
02_langgraph/         — LangGraph (OpenAI backend)
03_strands/           — Strands Agents (AWS Bedrock / Claude)
04_google_adk/        — Google ADK (Gemini)
05_mcp/               — Model Context Protocol: using and building MCP servers
patterns/             — Cross-framework comparisons
  react/              ✅ complete
  plan_and_execute/   🚧 stubs
  reflection/         🚧 stubs
  multi_agent/        🚧 stubs
06_claude_code/       — How Claude Code works; 9-session progression (Anthropic API, no framework)
```

## LLM Backends

- `01_langchain/`, `02_langgraph/`: OpenAI (`gpt-4o-mini`)
- `03_strands/`: Amazon Bedrock (Claude, via AWS credentials)
- `04_google_adk/`: Gemini (`gemini-2.0-flash`)
- `05_mcp/`: Anthropic API directly (`claude-opus-4-6`) + MCP Python SDK
- `06_claude_code/`: Anthropic API directly (`claude-opus-4-6`)

## Architecture Notes

**06_claude_code sessions:** Each session adds one mechanism without changing the core loop. All 9 sessions are complete, working implementations.

**Google ADK** is async-first — all scripts use `asyncio.run(main())`. ADK tools must return `dict`.

**Strands** tools are plain Python functions decorated with `@tool`; return values can be any type.

**Tool docstrings** are the tool descriptions the LLM reads — write them for the model, not the developer.

## Adding New Content

- Follow the numbering within each section (`05_`, `06_`, etc.)
- For `patterns/`: implement the same task across all 4 frameworks for direct comparison
- `06_claude_code` sessions should each add **one mechanism only**
