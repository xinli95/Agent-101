"""
Basic LangGraph — Hello World
==============================
The simplest possible LangGraph application.

Covers: StateGraph, TypedDict state, nodes, edges, compiling, and invoking.

Graph:  [START] → extract_name → generate_response → [END]

Run:
    python 02_langgraph/01_basic_graph/graph.py
"""

from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

load_dotenv()


# 1. Define state — a TypedDict that flows through every node.
#    Each node receives the full state and returns a partial update.
class State(TypedDict):
    messages: list
    user_name: str


# 2. Define nodes — plain Python functions: (State) -> dict
def extract_name(state: State) -> dict:
    """Parse a name from the first message (naive string split)."""
    content = state["messages"][-1].content
    name = content.split("name is ")[-1].strip("!.") if "name is " in content else "stranger"
    return {"user_name": name}


def generate_response(state: State) -> dict:
    """Generate a personalized greeting using the LLM."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    prompt = f"Write a warm, one-sentence welcome for {state['user_name']} who is learning about AI agents."
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"messages": state["messages"] + [response]}


# 3. Build and compile the graph
def build_graph():
    graph = StateGraph(State)

    graph.add_node("extract_name", extract_name)
    graph.add_node("generate_response", generate_response)

    graph.add_edge(START, "extract_name")
    graph.add_edge("extract_name", "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()


def main():
    app = build_graph()

    test_inputs = [
        "Hi, my name is Alice!",
        "Hello, my name is Bob. Nice to meet you.",
    ]

    for message in test_inputs:
        print(f"\nInput: {message}")
        result = app.invoke({"messages": [HumanMessage(content=message)], "user_name": ""})
        print(f"Name extracted: {result['user_name']}")
        print(f"Response: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
