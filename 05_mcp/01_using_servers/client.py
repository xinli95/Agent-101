"""
Using Existing MCP Servers
============================
Connect to an MCP server, discover its tools, and call them programmatically.

The same client code works with any MCP server — Python or Node.js.
The server is just a subprocess communicating over stdio.

This script connects to two servers:
  1. Our own Python server from 02_building_server/ (no extra setup needed)
  2. The official Filesystem server via npx (requires Node.js 18+)

Run:
    python 05_mcp/01_using_servers/client.py
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

SERVER_SCRIPT = str(Path(__file__).parent.parent / "02_building_server" / "server.py")


async def inspect_server(server_params: StdioServerParameters, label: str) -> None:
    """Connect to an MCP server and print its capabilities."""
    print(f"\n{'='*55}")
    print(f"  Server: {label}")
    print(f"{'='*55}")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # --- Tools ---
            tools_result = await session.list_tools()
            print(f"\nTools ({len(tools_result.tools)}):")
            for tool in tools_result.tools:
                schema = tool.inputSchema.get("properties", {})
                params = ", ".join(f"{k}: {v.get('type', '?')}" for k, v in schema.items())
                print(f"  • {tool.name}({params})")
                print(f"    {tool.description}")

            # --- Resources ---
            try:
                resources_result = await session.list_resources()
                if resources_result.resources:
                    print(f"\nResources ({len(resources_result.resources)}):")
                    for r in resources_result.resources:
                        print(f"  • {r.uri}  —  {r.description or r.name}")
            except Exception:
                pass  # Not all servers expose resources

            # --- Demo: call a tool ---
            if tools_result.tools:
                first_tool = tools_result.tools[0]
                print(f"\nDemo — calling '{first_tool.name}':")

                # Build minimal args using the schema's required fields
                required = first_tool.inputSchema.get("required", [])
                props = first_tool.inputSchema.get("properties", {})
                demo_args = {}
                for key in required:
                    typ = props.get(key, {}).get("type", "string")
                    demo_args[key] = "2 + 2" if typ == "string" else 42

                result = await session.call_tool(first_tool.name, demo_args)
                for content in result.content:
                    if hasattr(content, "text"):
                        print(f"  Result: {content.text}")


async def demo_python_server() -> None:
    """Connect to the Python MCP server in 02_building_server/."""
    params = StdioServerParameters(command="python", args=[SERVER_SCRIPT])
    await inspect_server(params, "Custom Python server (02_building_server/server.py)")


async def demo_filesystem_server() -> None:
    """Connect to the official MCP Filesystem server (requires Node.js + npx)."""
    import shutil

    if not shutil.which("npx"):
        print("\n[filesystem server] Skipped — npx not found. Install Node.js 18+ to run.")
        return

    cwd = str(Path.cwd())
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", cwd],
    )
    await inspect_server(params, f"Filesystem server (root: {cwd})")


async def main() -> None:
    print("MCP Client Demo — connecting to servers and inspecting their tools.\n")
    await demo_python_server()
    await demo_filesystem_server()


if __name__ == "__main__":
    asyncio.run(main())
