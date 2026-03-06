"""
Building an MCP Server with FastMCP
======================================
FastMCP is the high-level Python SDK for building MCP servers.
Decorate Python functions with @mcp.tool() and they become
LLM-callable tools automatically — docstrings become descriptions,
type hints become the JSON Schema.

This server exposes three tools:
  - calculator: evaluate math expressions
  - get_weather: simulated weather lookup
  - word_count: count words and characters in text

Run standalone (stdio transport):
    python 05_mcp/02_building_server/server.py

Test with the MCP inspector:
    npx @modelcontextprotocol/inspector python 05_mcp/02_building_server/server.py

Use from a client:
    See 01_using_servers/client.py and 03_agent_with_mcp/agent.py
"""

import math

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("agent-101-demo")


@mcp.tool()
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression and return the result.

    Supports standard Python math syntax and all functions from the math module:
    sqrt, sin, cos, log, pow, pi, e, etc.

    Examples: '2 + 2', 'sqrt(144)', '2 ** 10', 'sin(pi / 2)'
    """
    try:
        result = eval(expression, {"__builtins__": {}}, vars(math))
        return str(result)
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


@mcp.tool()
def get_weather(city: str, units: str = "celsius") -> str:
    """Get the current weather for a city.

    Args:
        city: Name of the city (e.g., 'Tokyo', 'New York', 'London')
        units: Temperature units — 'celsius' or 'fahrenheit' (default: celsius)

    Returns a summary of current conditions and temperature.
    """
    weather_db = {
        "tokyo":    {"temp_c": 22, "condition": "sunny", "humidity": 60},
        "new york": {"temp_c": 18, "condition": "partly cloudy", "humidity": 55},
        "london":   {"temp_c": 14, "condition": "rainy", "humidity": 80},
        "paris":    {"temp_c": 16, "condition": "overcast", "humidity": 70},
        "sydney":   {"temp_c": 25, "condition": "clear", "humidity": 50},
    }

    data = weather_db.get(city.lower())
    if not data:
        available = ", ".join(weather_db.keys())
        return f"No data for '{city}'. Available cities: {available}"

    temp = data["temp_c"]
    if units.lower() == "fahrenheit":
        temp = round(temp * 9 / 5 + 32, 1)
        unit_str = "°F"
    else:
        unit_str = "°C"

    return (
        f"{city.title()}: {data['condition']}, "
        f"{temp}{unit_str}, humidity {data['humidity']}%"
    )


@mcp.tool()
def word_count(text: str) -> str:
    """Count words, characters, and sentences in a text string.

    Args:
        text: The input text to analyze.

    Returns a breakdown of word count, character count (with and without spaces),
    and estimated sentence count.
    """
    words = text.split()
    chars_with_spaces = len(text)
    chars_no_spaces = len(text.replace(" ", ""))
    sentences = len([s for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()])

    return (
        f"Words: {len(words)} | "
        f"Characters: {chars_with_spaces} (with spaces), {chars_no_spaces} (without) | "
        f"Sentences: {sentences}"
    )


if __name__ == "__main__":
    # Default transport is stdio — reads from stdin, writes to stdout.
    # This is the standard way MCP servers are launched by clients.
    mcp.run(transport="stdio")
