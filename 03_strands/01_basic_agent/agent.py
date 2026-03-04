"""
Basic Agent with Strands
=========================
The minimal Strands agent: define tools with @tool, pass them to Agent(),
and invoke with a natural language query.

Strands handles the tool loop automatically via Amazon Bedrock (Claude by default).
No manual loop, no prompt templates — just tools and a system prompt.

Run:
    python 03_strands/01_basic_agent/agent.py
"""

import math

from dotenv import load_dotenv
from strands import Agent, tool

load_dotenv()


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.
    Examples: '2 + 2', '10 * 5', 'sqrt(144)', '2 ** 10'
    """
    try:
        return str(eval(expression, {"__builtins__": {}}, vars(math)))
    except Exception as e:
        return f"Error: {e}"


@tool
def count_letters(text: str) -> int:
    """Count the number of letters (a-z, A-Z) in a text string, excluding spaces."""
    return sum(c.isalpha() for c in text)


def main():
    # Strands defaults to Amazon Bedrock with Claude (claude-3-5-haiku-20251022)
    agent = Agent(
        tools=[calculator, count_letters],
        system_prompt="You are a helpful assistant that can perform calculations and text analysis.",
    )

    queries = [
        "What is 15% of 847?",
        "How many letters are in the phrase 'artificial intelligence'?",
        "What is 2 to the power of 16?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        response = agent(query)
        print(f"Response: {response}")


if __name__ == "__main__":
    main()
