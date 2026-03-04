"""
Multi-Agent Orchestration with Strands
========================================
Agent-as-tool pattern: wrap specialized sub-agents as callable tools
so an orchestrator agent can delegate to them.

This is the Strands approach to multi-agent: no framework-level routing,
just agents calling agents through the standard tool interface.

Run:
    python 03_strands/03_multi_agent/multi_agent.py
"""

from dotenv import load_dotenv
from strands import Agent, tool

load_dotenv()

# --- Specialist sub-agents ---

_research_agent = Agent(
    system_prompt="You are a research specialist. Provide concise, factual information on any topic. 2-3 sentences max.",
)

_writer_agent = Agent(
    system_prompt="You are a writing specialist. Transform information into clear, engaging prose. 1 paragraph max.",
)


# --- Wrap sub-agents as tools the orchestrator can call ---

@tool
def research(topic: str) -> str:
    """Research a topic and return key facts. Use this to gather information before writing."""
    return str(_research_agent(f"Research this topic: {topic}"))


@tool
def write_content(research_notes: str) -> str:
    """Transform research notes into polished, readable prose."""
    return str(_writer_agent(f"Write a polished paragraph based on:\n{research_notes}"))


def main():
    orchestrator = Agent(
        tools=[research, write_content],
        system_prompt="""You are an orchestrator for content creation tasks.
Always follow this sequence:
1. Call 'research' to gather information on the topic
2. Call 'write_content' with the research results to produce the final output
Never answer directly from your own knowledge — always use the specialist tools.""",
    )

    tasks = [
        "Explain what the ReAct pattern is for AI agents.",
        "Describe how Amazon Bedrock fits into the AWS AI ecosystem.",
    ]

    for task in tasks:
        print(f"\n{'='*60}\nTask: {task}\n{'='*60}")
        result = orchestrator(task)
        print(f"\nResult:\n{result}")


if __name__ == "__main__":
    main()
