"""
Multi-Agent Collaboration in LangGraph
=======================================
Two specialized agents collaborate as subgraphs within a parent graph.

Unlike the supervisor pattern (centralized routing), this demonstrates
agent handoffs: agents communicate via shared state and pass control
directly to each other based on task completion.

Architecture:
  - Research subgraph: gathers and structures information
  - Writing subgraph: transforms research into polished output
  - Coordinator: sequences the subgraphs and merges results

Run:
    python 02_langgraph/04_multi_agent/multi_agent.py
"""

from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()


class SharedState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    research_output: str
    final_output: str


def build_research_subgraph(llm: ChatOpenAI) -> StateGraph:
    def research_node(state: SharedState) -> dict:
        task = state["messages"][0].content
        response = llm.invoke([
            SystemMessage(content="You are a research specialist. Summarize key facts concisely."),
            HumanMessage(content=f"Research this topic: {task}"),
        ])
        return {"research_output": response.content}

    graph = StateGraph(SharedState)
    graph.add_node("research", research_node)
    graph.add_edge(START, "research")
    graph.add_edge("research", END)
    return graph.compile()


def build_writing_subgraph(llm: ChatOpenAI) -> StateGraph:
    def writing_node(state: SharedState) -> dict:
        response = llm.invoke([
            SystemMessage(content="You are a writing specialist. Transform research into clear, engaging prose."),
            HumanMessage(content=f"Write a polished paragraph based on this research:\n{state['research_output']}"),
        ])
        return {"final_output": response.content}

    graph = StateGraph(SharedState)
    graph.add_node("write", writing_node)
    graph.add_edge(START, "write")
    graph.add_edge("write", END)
    return graph.compile()


def build_coordinator():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    research_graph = build_research_subgraph(llm)
    writing_graph = build_writing_subgraph(llm)

    def run_research(state: SharedState) -> dict:
        return research_graph.invoke(state)

    def run_writing(state: SharedState) -> dict:
        return writing_graph.invoke(state)

    graph = StateGraph(SharedState)
    graph.add_node("researcher", run_research)
    graph.add_node("writer", run_writing)

    graph.add_edge(START, "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


def main():
    coordinator = build_coordinator()

    tasks = [
        "The ReAct pattern for AI agents",
        "How LangGraph differs from LangChain",
    ]

    for task in tasks:
        print(f"\n{'='*60}\nTask: {task}\n{'='*60}")
        result = coordinator.invoke({
            "messages": [HumanMessage(content=task)],
            "research_output": "",
            "final_output": "",
        })
        print(f"\nResearch:\n{result['research_output']}")
        print(f"\nFinal Output:\n{result['final_output']}")


if __name__ == "__main__":
    main()
