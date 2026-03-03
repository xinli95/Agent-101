"""
Multi-Agent with Google ADK
============================
ADK supports hierarchical multi-agent systems via AgentTool:
a parent agent can invoke child agents as if they were tools.

Architecture:
  orchestrator
    ├── researcher (sub-agent via AgentTool)
    └── writer     (sub-agent via AgentTool)

Run:
    python 04_google_adk/03_multi_agent/multi_agent.py
"""

import asyncio

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import AgentTool, FunctionTool
from google.genai import types

load_dotenv()


def research_topic(topic: str) -> dict:
    """Simulate researching a topic (replace with real search in production).

    Args:
        topic: The topic to research.

    Returns:
        A dict with 'topic' and 'findings' keys.
    """
    return {
        "topic": topic,
        "findings": f"Key facts about '{topic}': [simulated research — connect a real search API here]",
    }


async def main():
    # Sub-agent: specialized researcher
    researcher = Agent(
        name="researcher",
        model="gemini-2.0-flash",
        description="Specialist for researching topics and returning structured facts.",
        instruction="Research topics thoroughly. Return concise, factual summaries in 2-3 sentences.",
        tools=[FunctionTool(research_topic)],
    )

    # Sub-agent: specialized writer
    writer = Agent(
        name="writer",
        model="gemini-2.0-flash",
        description="Specialist for transforming information into polished prose.",
        instruction="Transform the provided information into a clear, engaging paragraph.",
        tools=[],
    )

    # Orchestrator: delegates to sub-agents via AgentTool
    orchestrator = Agent(
        name="orchestrator",
        model="gemini-2.0-flash",
        description="Orchestrates research and writing tasks.",
        instruction="""For content creation tasks, always follow this sequence:
1. Delegate to the 'researcher' agent to gather information.
2. Pass the research to the 'writer' agent to produce polished output.
Never answer directly from your own knowledge.""",
        tools=[AgentTool(agent=researcher), AgentTool(agent=writer)],
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=orchestrator, app_name="multi-agent-adk", session_service=session_service)
    session = await session_service.create_session(app_name="multi-agent-adk", user_id="user-1")

    task = "Create a short explanation of what the ReAct pattern is for AI agents."
    print(f"Task: {task}\n")

    content = types.Content(role="user", parts=[types.Part(text=task)])
    async for event in runner.run_async(user_id="user-1", session_id=session.id, new_message=content):
        if event.is_final_response():
            print(f"Result:\n{event.response.parts[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
