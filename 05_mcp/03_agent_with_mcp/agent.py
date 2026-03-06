"""
Agent with MCP Tools
======================
A full agent loop where tools are discovered dynamically from an MCP server
at runtime — not hardcoded. The agent doesn't know what tools exist until
it connects and asks.

This is the key power of MCP: swap the server and the agent gets a completely
different set of capabilities without any code changes.

How it works:
  1. Connect to the MCP server via stdio
  2. Fetch the tool list → convert to Anthropic format
  3. Pass tools to the LLM — standard Anthropic tool-use loop
  4. When the LLM calls a tool, forward the call to the MCP server
  5. Return the result to the LLM and continue

Run:
    python 05_mcp/03_agent_with_mcp/agent.py

Swap the server:
    Edit SERVER_PARAMS at the bottom to point to any other MCP server.
    The agent loop requires zero changes.
"""

import asyncio
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

anth = anthropic.Anthropic()

SERVER_SCRIPT = str(Path(__file__).parent.parent / "02_building_server" / "server.py")


# --- MCP ↔ Anthropic bridge ---

def mcp_tools_to_anthropic(mcp_tools) -> list[dict]:
    """Convert MCP tool definitions to Anthropic's tool format.

    The only difference: MCP uses 'inputSchema' (camelCase),
    Anthropic expects 'input_schema' (snake_case).
    """
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,
        }
        for tool in mcp_tools
    ]


async def call_mcp_tool(session: ClientSession, name: str, args: dict) -> str:
    """Call a tool on the MCP server and return its text output."""
    result = await session.call_tool(name, args)
    return "\n".join(
        block.text for block in result.content if hasattr(block, "text")
    )


# --- Agent loop ---

async def agent_loop(session: ClientSession, user_message: str) -> str:
    """Standard Anthropic tool-use loop, with MCP as the tool backend."""

    # Discover tools fresh on each call (servers can add tools dynamically)
    tools_result = await session.list_tools()
    tools = mcp_tools_to_anthropic(tools_result.tools)

    messages = [{"role": "user", "content": user_message}]

    while True:
        response = anth.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=(
                "You are a helpful assistant with access to MCP tools. "
                "Use them to answer questions accurately."
            ),
            messages=messages,
            tools=tools,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        # Forward every tool call to the MCP server
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [mcp → {block.name}] {block.input}")
                output = await call_mcp_tool(session, block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

        messages.append({"role": "user", "content": tool_results})


# --- Main ---

async def main() -> None:
    # Point this at any MCP server — Python, Node.js, or remote via HTTP.
    # The agent loop below requires zero changes.
    server_params = StdioServerParameters(
        command="python",
        args=[SERVER_SCRIPT],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Show what tools are available
            tools_result = await session.list_tools()
            print(f"Connected to MCP server — {len(tools_result.tools)} tools available:")
            for tool in tools_result.tools:
                print(f"  • {tool.name}: {tool.description.splitlines()[0]}")
            print()

            queries = [
                "What is sqrt(225) and what is 2 to the power of 8?",
                "What's the weather in Tokyo and London? Give me celsius for both.",
                "Count the words and characters in: 'The quick brown fox jumps over the lazy dog.'",
            ]

            for query in queries:
                print(f"Query: {query}")
                answer = await agent_loop(session, query)
                print(f"Answer: {answer}\n")

            # Interactive mode
            print("─" * 55)
            print("Interactive mode — type your question or 'exit' to quit.\n")
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() in ("exit", "quit", "q") or not user_input:
                    break
                print()
                answer = await agent_loop(session, user_input)
                print(f"Agent: {answer}\n")


if __name__ == "__main__":
    asyncio.run(main())
