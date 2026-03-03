"""
ReAct Agent with LangChain
==========================
Demonstrates the ReAct (Reasoning + Acting) pattern:
  Thought → Action → Observation → Thought → ...

The agent uses a text-based prompt to reason step-by-step and decide
when to call tools. Set verbose=True in AgentExecutor to see the loop.

Run:
    python 01_langchain/01_react_agent/agent.py
"""

import math

from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Input must be a valid Python math expression.
    Examples: '2 + 2', '10 * 5', 'sqrt(144)', '2 ** 10'
    """
    try:
        result = eval(expression, {"__builtins__": {}}, vars(math))
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@tool
def count_letters(text: str) -> str:
    """Count the number of letters (a-z, A-Z) in a text string, excluding spaces and punctuation."""
    return str(sum(c.isalpha() for c in text))


def main():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [calculator, count_letters]

    # Pull the standard ReAct prompt from LangChain Hub.
    # It formats the loop as: Thought / Action / Action Input / Observation
    prompt = hub.pull("hwchase17/react")

    agent = create_react_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)

    questions = [
        "What is 15% of 847?",
        "How many letters are in the phrase 'artificial intelligence'?",
        "If I invest $10,000 at 7% annual return for 10 years using compound interest P*(1+r)**t, what do I get?",
    ]

    for question in questions:
        print(f"\n{'='*60}\nQuestion: {question}\n{'='*60}")
        result = executor.invoke({"input": question})
        print(f"\nFinal Answer: {result['output']}")


if __name__ == "__main__":
    main()
