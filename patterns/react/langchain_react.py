"""
ReAct Pattern — LangChain
==========================
Task: What is sqrt(144), and how many letters are in 'artificial intelligence'?

Framework: LangChain + AgentExecutor
LLM: OpenAI gpt-4o-mini
"""

import math

from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

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
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [calculator, count_letters]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    print(f"Task: {TASK}\n")
    result = executor.invoke({"input": TASK})
    print(f"\nAnswer: {result['output']}")
