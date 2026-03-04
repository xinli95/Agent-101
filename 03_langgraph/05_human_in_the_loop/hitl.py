"""
Human-in-the-Loop with LangGraph
==================================
The agent pauses before a consequential action, waits for human approval,
then continues (or stops) based on that feedback.

Key LangGraph features used:
- interrupt_before: pause execution before a named node
- MemorySaver: persist state across interruptions (checkpointing)
- update_state: inject human feedback into the paused graph

Use case: an agent proposes a plan for a sensitive task (code refactor,
email, database migration) and asks for approval before executing it.

Run:
    python 02_langgraph/05_human_in_the_loop/hitl.py
"""

from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    action_plan: str
    approved: bool


def planner_node(state: State) -> dict:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    task = state["messages"][-1].content
    response = llm.invoke([HumanMessage(content=f"Create a concise 3-step action plan for: {task}")])
    return {
        "action_plan": response.content,
        "messages": [AIMessage(content=f"Proposed plan:\n{response.content}")],
    }


def human_review_node(state: State) -> dict:
    # This node is interrupted BEFORE execution via interrupt_before=["human_review"].
    # The graph pauses here; the caller uses app.update_state() to set approved=True/False,
    # then resumes with app.invoke(None, thread_config).
    return {}


def executor_node(state: State) -> dict:
    if not state.get("approved", False):
        return {"messages": [AIMessage(content="Execution cancelled — plan was not approved.")]}
    return {"messages": [AIMessage(content=f"Executing approved plan...\n\n✓ All steps complete.")]}


def build_graph():
    memory = MemorySaver()
    graph = StateGraph(State)

    graph.add_node("planner", planner_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("executor", executor_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "human_review")
    graph.add_edge("human_review", "executor")
    graph.add_edge("executor", END)

    return graph.compile(checkpointer=memory, interrupt_before=["human_review"])


def main():
    app = build_graph()
    thread = {"configurable": {"thread_id": "demo-session"}}
    task = "Migrate our user authentication from session cookies to JWT tokens"

    print(f"Task: {task}\n")

    # Step 1: Run until the interrupt (stops before human_review)
    state = app.invoke(
        {"messages": [HumanMessage(content=task)], "action_plan": "", "approved": False},
        thread,
    )
    print(state["messages"][-1].content)

    # Step 2: Human reviews the plan
    approval = input("\nApprove this plan? (y/n): ").strip().lower()
    app.update_state(thread, {"approved": approval == "y"})

    # Step 3: Resume — graph continues from human_review → executor
    final = app.invoke(None, thread)
    print(f"\n{final['messages'][-1].content}")


if __name__ == "__main__":
    main()
