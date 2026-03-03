"""
Plan-and-Execute Pattern — LangChain
======================================
Task: [same task as react/ comparisons]

The agent first creates a full multi-step plan, then executes each step.
Contrast with ReAct: the plan is fixed upfront vs. reasoning step-by-step.

TODO: Implement using:
- A planner chain: LLM → structured list of steps
- An executor loop: for each step, call the appropriate tool
- Optional replanning: if a step fails, regenerate the remaining plan
"""
