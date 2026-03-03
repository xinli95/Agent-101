"""
Plan-and-Execute Pattern — LangGraph
======================================
Task: [same task as react/ comparisons]

LangGraph makes Plan-and-Execute natural: a "planner" node generates steps,
then a loop node executes them one by one, updating shared state.

TODO: Implement using:
- State: { plan: list[str], current_step: int, results: list[str] }
- planner_node: LLM generates the full plan
- executor_node: runs the current step using tools
- Conditional edge: continue loop if steps remain, else END
"""
