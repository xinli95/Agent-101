"""
Reflection Pattern — LangChain
================================
The agent generates a draft, critiques it, then revises based on the critique.
Repeat until quality threshold is met or max iterations reached.

TODO: Implement using:
- A generator chain: task → draft
- A critic chain: draft → critique (what's wrong? what's missing?)
- A reviser chain: draft + critique → improved draft
- A loop with a stopping condition (e.g., critique says "looks good" or max_iterations)
"""
