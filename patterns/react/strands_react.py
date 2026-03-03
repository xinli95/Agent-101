"""
ReAct Pattern — Strands Agents
================================
Task: What is sqrt(144), and how many letters are in 'artificial intelligence'?

Framework: AWS Strands Agents
LLM: Amazon Bedrock (Claude by default)

Compare with the other react/ files — notice how Strands requires
the least boilerplate: just tools and an Agent().
"""

import math

from dotenv import load_dotenv
from strands import Agent, tool

load_dotenv()

TASK = "What is sqrt(144)? And how many letters (not spaces) are in 'artificial intelligence'?"


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Examples: 'sqrt(144)', '2 ** 10'"""
    try:
        return str(eval(expression, {"__builtins__": {}}, vars(math)))
    except Exception as e:
        return f"Error: {e}"


@tool
def count_letters(text: str) -> str:
    """Count letters (a-z, A-Z) in a string, excluding spaces and punctuation."""
    return str(sum(c.isalpha() for c in text))


if __name__ == "__main__":
    agent = Agent(
        tools=[calculator, count_letters],
        system_prompt="Use tools to answer questions precisely.",
    )

    print(f"Task: {TASK}\n")
    result = agent(TASK)
    print(f"\nAnswer: {result}")
