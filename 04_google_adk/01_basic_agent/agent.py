"""
Basic Agent with Google ADK
============================
The minimal Google ADK agent: define tools as plain functions,
wrap them with FunctionTool, create an Agent, and run via Runner.

ADK is async-first. All agent invocations go through asyncio.

Run:
    python 04_google_adk/01_basic_agent/agent.py
"""

import asyncio
import math

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

load_dotenv()


def calculator(expression: str) -> dict:
    """Evaluate a mathematical expression.

    Args:
        expression: A valid Python math expression, e.g., '2 + 2', 'sqrt(144)', '2 ** 10'

    Returns:
        A dict with a 'result' key containing the answer as a string,
        or an 'error' key if the expression is invalid.
    """
    try:
        result = eval(expression, {"__builtins__": {}}, vars(math))
        return {"result": str(result)}
    except Exception as e:
        return {"error": str(e)}


def count_letters(text: str) -> dict:
    """Count the number of letters (a-z, A-Z) in a text string, excluding spaces.

    Args:
        text: The input text to count letters in.

    Returns:
        A dict with a 'count' key containing the letter count.
    """
    return {"count": sum(c.isalpha() for c in text)}


async def main():
    agent = Agent(
        name="math_agent",
        model="gemini-2.0-flash",
        description="A helpful agent for calculations and text analysis.",
        instruction="Use your tools to answer questions precisely. Always use tools rather than computing mentally.",
        tools=[FunctionTool(calculator), FunctionTool(count_letters)],
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="agent-101-basic", session_service=session_service)
    session = await session_service.create_session(app_name="agent-101-basic", user_id="user-1")

    queries = [
        "What is 15% of 847?",
        "How many letters are in 'artificial intelligence'?",
        "What is 2 to the power of 16?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        content = types.Content(role="user", parts=[types.Part(text=query)])
        async for event in runner.run_async(user_id="user-1", session_id=session.id, new_message=content):
            if event.is_final_response():
                print(f"Response: {event.response.parts[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
