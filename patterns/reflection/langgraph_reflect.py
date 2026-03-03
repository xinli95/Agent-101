"""
Reflection Pattern — LangGraph
================================
The same reflection loop as langchain_reflect.py, built as a LangGraph graph.

LangGraph's explicit loop control makes the iteration easy to visualize and debug.

TODO: Implement using:
- State: { draft: str, critique: str, iteration: int }
- generate_node: produce initial draft or revision
- critique_node: evaluate the draft, identify weaknesses
- Conditional edge from critique_node:
    - if "APPROVED" in critique or iteration >= MAX: → END
    - else: → generate_node (with critique in state)
"""
