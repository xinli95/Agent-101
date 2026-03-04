# LangGraph

LangGraph builds on LangChain to add **stateful, graph-based orchestration**. Where LangChain's AgentExecutor is a black box, LangGraph gives you explicit control over every node and edge in the agent loop.

The key insight: agent behavior is a graph. Nodes are functions; edges are transitions. Cycles enable loops.

## Examples

| # | Script | Concept |
|---|--------|---------|
| 01 | `01_basic_graph/graph.py` | Nodes, edges, state, compiling — the LangGraph "hello world" |
| 02 | `02_react_agent/agent.py` | ReAct reimplemented from scratch as a graph |
| 03 | `03_supervisor_pattern/supervisor.py` | Supervisor routing to specialized workers |
| 04 | `04_multi_agent/multi_agent.py` | Agents as subgraphs calling other agents |
| 05 | `05_human_in_the_loop/hitl.py` | Interrupt before a node for human approval |

## Setup

```bash
pip install -e ".[langgraph]"
cp .env.example .env  # add OPENAI_API_KEY
```

## Key Concepts

- `StateGraph` — The main graph class. Takes a TypedDict that defines the shared state.
- `add_messages` — A reducer that appends to a list instead of overwriting it. Used for message history.
- `ToolNode` — A prebuilt node that executes tool calls from the last AI message.
- `tools_condition` — Routes to `"tools"` if the last message has tool calls, else to `END`.
- `interrupt_before` — Pauses execution before a named node so a human can review state.
- `MemorySaver` — In-memory checkpointer for persisting state across interrupts.
