# Patterns — Cross-Framework Comparisons

Each subdirectory implements the **same problem** across all four frameworks.
Reading these side-by-side is the fastest way to understand the tradeoffs.

## Available Comparisons

| Pattern | Description | Status |
|---------|-------------|--------|
| [react/](react/) | ReAct loop: same math+text task in all 4 frameworks | ✅ Complete |
| [plan_and_execute/](plan_and_execute/) | Plan first, then execute each step | 🚧 In progress |
| [reflection/](reflection/) | Agent critiques and improves its own output | 🚧 In progress |
| [multi_agent/](multi_agent/) | Agents collaborating on a shared task | 🚧 In progress |

## How to Read These

1. Pick a pattern directory.
2. Open all four files side-by-side.
3. Notice what stays the same (the agent logic) vs. what changes (the framework API).

The task is always identical so differences are purely framework-driven.
