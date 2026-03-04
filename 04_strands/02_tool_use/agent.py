"""
Advanced Tool Use with Strands
================================
Demonstrates multiple custom tools alongside Strands' built-in tools.

Strands ships with prebuilt tools for common operations (HTTP requests,
Python REPL, file I/O, etc.) that you can drop in alongside custom tools.

Run:
    python 03_strands/02_tool_use/agent.py
"""

import urllib.request

from dotenv import load_dotenv
from strands import Agent, tool
from strands.tools import use_aws  # Built-in: call AWS services directly

load_dotenv()


@tool
def get_weather(city: str) -> str:
    """Get current weather for a city using wttr.in (no API key needed).
    Returns a one-line weather summary.
    """
    try:
        url = f"https://wttr.in/{city.replace(' ', '+')}?format=3"
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.read().decode()
    except Exception as e:
        return f"Could not fetch weather for {city}: {e}"


@tool
def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between common units.
    Supported pairs: km/miles, celsius/fahrenheit, kg/pounds
    """
    conversions = {
        ("km", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x * 1.60934,
        ("celsius", "fahrenheit"): lambda x: x * 9 / 5 + 32,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5 / 9,
        ("kg", "pounds"): lambda x: x * 2.20462,
        ("pounds", "kg"): lambda x: x * 0.453592,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key not in conversions:
        return f"Unsupported: {from_unit} → {to_unit}. Supported: {list(conversions.keys())}"
    return f"{value} {from_unit} = {conversions[key](value):.2f} {to_unit}"


def main():
    agent = Agent(
        tools=[get_weather, unit_converter],
        system_prompt="You are a helpful assistant with weather and unit conversion capabilities.",
    )

    queries = [
        "What's the weather in Tokyo?",
        "Convert 25 celsius to fahrenheit and 100 km to miles.",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        response = agent(query)
        print(f"Response: {response}")


if __name__ == "__main__":
    main()
