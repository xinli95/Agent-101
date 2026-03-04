"""
Supervisor Pattern in LangGraph
================================
A supervisor agent routes incoming tasks to specialized worker agents.
After each worker responds, control returns to the supervisor, which
decides whether to call another worker or declare the task complete.

Graph:
  [START] → supervisor → researcher → supervisor → ...
                       ↘ writer    ↗
                       ↘ coder    ↗
                       ↘ [END] (when supervisor says FINISH)

Run:
    python 02_langgraph/03_supervisor_pattern/supervisor.py
"""

from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()

WORKERS = ["researcher", "writer", "coder"]
Route = Literal["researcher", "writer", "coder", "finish"]


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next: str


def make_supervisor(llm: ChatOpenAI):
    system = f"""You are a supervisor managing these specialists: {', '.join(WORKERS)}.

Given the conversation so far, decide who should act next — or respond FINISH if the task is done.
- researcher: finds and summarizes information
- writer: drafts documents, summaries, and prose
- coder: writes and explains Python code

Respond with exactly one word: a worker name or FINISH."""

    def node(state: State) -> dict:
        response = llm.invoke([SystemMessage(content=system)] + state["messages"])
        decision = response.content.strip().lower()
        if decision not in WORKERS + ["finish"]:
            decision = "finish"
        return {"next": decision, "messages": [response]}

    return node


def make_worker(name: str, description: str, llm: ChatOpenAI):
    system = f"You are a {name}. {description} Be concise and focused."

    def node(state: State) -> dict:
        # Workers see the original task (first message) plus any prior context
        response = llm.invoke([SystemMessage(content=system)] + state["messages"])
        # Tag the response with the worker's name so it's clear in the history
        tagged = HumanMessage(content=f"[{name.upper()}]: {response.content}")
        return {"messages": [tagged]}

    return node


def build_graph():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    graph = StateGraph(State)
    graph.add_node("supervisor", make_supervisor(llm))
    graph.add_node("researcher", make_worker("researcher", "You find and summarize factual information.", llm))
    graph.add_node("writer", make_worker("writer", "You write clear, engaging content.", llm))
    graph.add_node("coder", make_worker("coder", "You write clean, well-commented Python code.", llm))

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        lambda s: s["next"],
        {"researcher": "researcher", "writer": "writer", "coder": "coder", "finish": END},
    )
    for worker in WORKERS:
        graph.add_edge(worker, "supervisor")

    return graph.compile()


def main():
    app = build_graph()

    tasks = [
        "Write a Python function that checks if a number is prime, and include a brief explanation.",
        "Research what LangGraph is and write a 2-sentence summary for a developer audience.",
    ]

    for task in tasks:
        print(f"\n{'='*60}\nTask: {task}\n{'='*60}")
        result = app.invoke(
            {"messages": [HumanMessage(content=task)], "next": ""},
            {"recursion_limit": 10},
        )
        # Print the last substantive non-routing message
        for msg in reversed(result["messages"]):
            content = msg.content.strip()
            if content and content.lower() not in WORKERS + ["finish"]:
                print(f"\nResult:\n{content}")
                break


if __name__ == "__main__":
    main()
