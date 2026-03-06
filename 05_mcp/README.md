# Model Context Protocol (MCP)

MCP is an open standard by Anthropic that lets LLMs connect to external tools, data sources, and services through a unified interface — without changing the model or the application code.

Think of it as a USB-C standard for AI: any MCP-compatible client (Claude Desktop, Claude Code, your own app) can plug into any MCP server.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  MCP Host (your app / Claude Desktop)           │
│                                                 │
│  ┌───────────┐     ┌───────────┐               │
│  │ MCP Client│ ←──→│ MCP Client│  ...          │
│  └─────┬─────┘     └─────┬─────┘               │
└────────┼─────────────────┼─────────────────────┘
         │ stdio / HTTP+SSE │
    ┌────▼────┐        ┌────▼────────┐
    │  MCP    │        │  MCP        │
    │ Server  │        │ Server      │
    │(Python) │        │ (Node.js)   │
    └─────────┘        └─────────────┘
```

**Transports:**
- `stdio` — client spawns a subprocess and communicates via stdin/stdout. Best for local tools.
- `HTTP + SSE` — server runs independently; client connects over the network. Best for remote/shared servers.

## Core Primitives

| Primitive | Purpose | Example |
|-----------|---------|---------|
| **Tools** | Functions the LLM can call | `search_web(query)`, `run_sql(query)` |
| **Resources** | Data the LLM can read | `file://readme.md`, `db://users/42` |
| **Prompts** | Reusable prompt templates | `/summarize`, `/code-review` |

## Examples in This Section

| # | Script | What it shows |
|---|--------|---------------|
| 01 | `01_using_servers/client.py` | Connect to an existing MCP server, discover tools, call them |
| 02 | `02_building_server/server.py` | Build a custom MCP server with FastMCP |
| 03 | `03_agent_with_mcp/agent.py` | Full agent loop that uses MCP tools discovered at runtime |

## Setup

```bash
pip install -e ".[mcp]"
# Add ANTHROPIC_API_KEY to .env
```

For servers that run via Node.js (most of the open-source ecosystem):
```bash
node --version   # requires Node.js 18+
npx -y @modelcontextprotocol/server-filesystem .   # test it works
```

## Popular Open-Source MCP Servers

All available at [github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers).

| Server | Install | What it does |
|--------|---------|--------------|
| **Filesystem** | `npx @modelcontextprotocol/server-filesystem <path>` | Read/write local files |
| **GitHub** | `npx @modelcontextprotocol/server-github` | Repos, issues, PRs, code search |
| **Postgres** | `npx @modelcontextprotocol/server-postgres <conn-str>` | Query a PostgreSQL database |
| **Slack** | `npx @modelcontextprotocol/server-slack` | Read channels, post messages |
| **Brave Search** | `npx @modelcontextprotocol/server-brave-search` | Live web search |
| **Memory** | `npx @modelcontextprotocol/server-memory` | Persistent knowledge graph |
| **Fetch** | `uvx mcp-server-fetch` | HTTP fetching and web scraping |
| **Sequential Thinking** | `npx @modelcontextprotocol/server-sequential-thinking` | Structured step-by-step reasoning |

### Community Registry

Browse hundreds more at [mcp.so](https://mcp.so) and [mcpmarket.com](https://mcpmarket.com).

## How Claude Code Uses MCP

Claude Code itself is an MCP host. When you run `claude mcp add`, you're registering an MCP server that Claude Code will connect to automatically. The tools from that server become available to Claude the same way built-in tools are — the LLM simply calls them by name.

This is why MCP matters: build a server once, use it in Claude Desktop, Claude Code, your own app, or any other MCP-compatible host.
