"""
ReAct Pattern — LangGraph
==========================
Task: What is sqrt(144), and how many letters are in 'artificial intelligence'?

Framework: LangGraph StateGraph
LLM: OpenAI gpt-4o-mini

Compare with langchain_react.py — the agent logic is identical,
but we own the loop explicitly via graph nodes and edges.
"""

import math
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

TASK = "What is sqrt(144)? And how many letters (not spaces) are in 'artificial intelligence'?"


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


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
    tools = [calculator, count_letters]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)

    def agent_node(state: State) -> dict:
        return {"messages": [llm.invoke(state["messages"])]}

    graph = StateGraph(State)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    app = graph.compile()

    print(f"Task: {TASK}\n")
    result = app.invoke({"messages": [HumanMessage(content=TASK)]})
    print(f"\nAnswer: {result['messages'][-1].content}")
