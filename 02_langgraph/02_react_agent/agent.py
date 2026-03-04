"""
ReAct Agent in LangGraph
=========================
The ReAct loop built from scratch using LangGraph's StateGraph.

Compare with 01_langchain/01_react_agent — same pattern, but now you own
every step of the loop and can intercept, modify, or branch at any point.

Graph:
  [START] → agent → (has tool calls?) → tools → agent → ... → [END]
                  ↘ (no tool calls)  → [END]

Run:
    python 02_langgraph/02_react_agent/agent.py
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


# add_messages is a reducer: it appends new messages instead of overwriting
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Examples: '2 + 2', 'sqrt(144)', '2 ** 10'"""
    try:
        return str(eval(expression, {"__builtins__": {}}, vars(math)))
    except Exception as e:
        return f"Error: {e}"


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_react_agent():
    tools = [calculator, get_current_time]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState) -> dict:
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "agent")
    # tools_condition: if last message has tool_calls → "tools", else → END
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")  # after tools, return to agent

    return graph.compile()


def main():
    agent = build_react_agent()

    questions = [
        "What is 1337 * 42?",
        "What time is it right now?",
        "What is sqrt(2) rounded to 4 decimal places? Use round(sqrt(2), 4).",
    ]

    for question in questions:
        print(f"\n{'='*60}\nQuestion: {question}")
        result = agent.invoke({"messages": [HumanMessage(content=question)]})
        print(f"Answer: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
