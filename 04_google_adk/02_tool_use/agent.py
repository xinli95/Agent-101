"""
Tool Use with Google ADK
=========================
Custom tools alongside Google's built-in tools:
- google_search: live web search via Google Search API
- built_in_code_execution: execute Python code in a sandbox

Note: google_search requires a Google Search API key or Grounding with Google Search
enabled in your Gemini API / Vertex AI settings.

Run:
    python 04_google_adk/02_tool_use/agent.py
"""

import asyncio

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool, built_in_code_execution, google_search
from google.genai import types

load_dotenv()


def get_weather(city: str) -> dict:
    """Get current weather for a city.

    Args:
        city: Name of the city to get weather for.

    Returns:
        A dict with 'city', 'temperature', and 'condition' keys.
    """
    # Simulated data — replace with a real weather API in production
    weather_data = {
        "new york": {"temperature": "72°F", "condition": "partly cloudy"},
        "london": {"temperature": "58°F", "condition": "rainy"},
        "tokyo": {"temperature": "68°F", "condition": "sunny"},
        "paris": {"temperature": "65°F", "condition": "overcast"},
    }
    data = weather_data.get(city.lower(), {"temperature": "N/A", "condition": "unknown"})
    return {"city": city, **data}


async def main():
    agent = Agent(
        name="research_agent",
        model="gemini-2.0-flash",
        description="An agent with weather lookup, web search, and code execution.",
        instruction="Use the most appropriate tool for each question. Prefer running code over mental math.",
        tools=[
            FunctionTool(get_weather),
            google_search,            # Built-in: live Google Search
            built_in_code_execution,  # Built-in: sandboxed Python execution
        ],
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="agent-101-tools", session_service=session_service)
    session = await session_service.create_session(app_name="agent-101-tools", user_id="user-1")

    queries = [
        "What's the weather in Tokyo?",
        "Write and run Python code to compute the first 10 Fibonacci numbers.",
    ]

    for query in queries:
        print(f"\n{'='*50}\nQuery: {query}")
        content = types.Content(role="user", parts=[types.Part(text=query)])
        async for event in runner.run_async(user_id="user-1", session_id=session.id, new_message=content):
            if event.is_final_response():
                print(f"Response: {event.response.parts[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
