"""
ReAct Pattern — Google ADK
============================
Task: What is sqrt(144), and how many letters are in 'artificial intelligence'?

Framework: Google ADK
LLM: Gemini 2.0 Flash

Compare with the other react/ files — ADK is async-first,
tools return dicts, and execution goes through Runner + sessions.
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

TASK = "What is sqrt(144)? And how many letters (not spaces) are in 'artificial intelligence'?"


def calculator(expression: str) -> dict:
    """Evaluate a math expression.

    Args:
        expression: A valid Python math expression, e.g., 'sqrt(144)'

    Returns:
        dict with 'result' (str) or 'error' (str) key.
    """
    try:
        result = eval(expression, {"__builtins__": {}}, vars(math))
        return {"result": str(result)}
    except Exception as e:
        return {"error": str(e)}


def count_letters(text: str) -> dict:
    """Count letters (a-z, A-Z) in a string, excluding spaces and punctuation.

    Args:
        text: The input string.

    Returns:
        dict with 'count' (int) key.
    """
    return {"count": sum(c.isalpha() for c in text)}


async def main():
    agent = Agent(
        name="react_agent",
        model="gemini-2.0-flash",
        description="Agent that can do math and text analysis.",
        instruction="Use tools to answer questions. Always use tools rather than computing mentally.",
        tools=[FunctionTool(calculator), FunctionTool(count_letters)],
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="react-comparison", session_service=session_service)
    session = await session_service.create_session(app_name="react-comparison", user_id="user-1")

    print(f"Task: {TASK}\n")
    content = types.Content(role="user", parts=[types.Part(text=TASK)])
    async for event in runner.run_async(user_id="user-1", session_id=session.id, new_message=content):
        if event.is_final_response():
            print(f"\nAnswer: {event.response.parts[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
