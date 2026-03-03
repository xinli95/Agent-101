# Agent Design Patterns

## 1. ReAct (Reasoning + Acting)

The foundational pattern. The agent interleaves reasoning traces with tool calls.
Introduced in [Yao et al., 2022](https://arxiv.org/abs/2210.03629).

```
Thought: I need to find the weather in Paris.
Action:  get_weather("Paris")
Obs:     65°F, overcast

Thought: Now I have the weather. I can answer.
Answer:  The weather in Paris is 65°F and overcast.
```

**Strengths:** Interpretable, flexible, works well for open-ended tasks.
**Weaknesses:** Can get stuck in loops, expensive for simple tasks.
**Implemented in:** `01_langchain/01_react_agent`, `02_langgraph/02_react_agent`, `patterns/react/`

---

## 2. Tool Calling (Structured Output)

The LLM uses the model's native function-calling API rather than text-based ReAct prompting.
More reliable than ReAct for structured tasks; less interpretable.

```
User  → LLM → { tool: "get_weather", args: { city: "Paris" } }
             ↓
           Tool executes
             ↓
       LLM incorporates result → Final answer
```

**Strengths:** Reliable, parallel tool calls, no prompt hacking.
**Weaknesses:** Less flexible reasoning, depends on model's function-calling quality.
**Implemented in:** `01_langchain/02_tool_calling`

---

## 3. Plan-and-Execute

The agent first creates a full plan, then executes each step.
Contrast with ReAct, which reasons step-by-step.

```
Step 1: Plan
  - Search for recent AI agent frameworks
  - Compare their features
  - Write a summary

Step 2: Execute each step in sequence (or in parallel)
```

**Strengths:** Better for long-horizon tasks, more predictable, easier to audit.
**Weaknesses:** Plan can become stale as new information arrives.
**Implemented in:** `patterns/plan_and_execute/`

---

## 4. Reflection

The agent evaluates its own output and iterates to improve it.

```
Draft → Critique → Revise → Critique → Revise → Final
```

**Strengths:** Higher quality output, catches errors.
**Weaknesses:** More LLM calls, can over-correct.
**Implemented in:** `patterns/reflection/`

---

## 5. Supervisor / Router

A supervisor agent routes tasks to specialized workers based on the task type.

```
                  ┌─ Researcher ─┐
User → Supervisor ─┤             ├─ Supervisor → User
                  └─ Writer ────┘
                  └─ Coder ─────┘
```

**Strengths:** Each agent can be specialized and independently improved.
**Weaknesses:** Supervisor becomes a bottleneck; routing errors cascade.
**Implemented in:** `02_langgraph/03_supervisor_pattern`

---

## 6. Multi-Agent (Swarm / Hierarchical)

Multiple agents collaborate without a central supervisor. Agents hand off to each other
based on capability or context.

```
Agent A ──handoff──► Agent B ──handoff──► Agent C
```

**Strengths:** Parallelism, no single point of failure, agents can specialize deeply.
**Weaknesses:** Hard to debug, coordination overhead, potential infinite loops.
**Implemented in:** `02_langgraph/04_multi_agent`, `03_strands/03_multi_agent`, `04_google_adk/03_multi_agent`, `patterns/multi_agent/`

---

## 7. Human-in-the-Loop (HITL)

The agent pauses at a checkpoint for human review before taking a consequential action.

```
Plan → [PAUSE: human reviews] → Approved? → Execute
                                           ↘ Modify → Re-plan
```

**Strengths:** Safety, trust, handles edge cases gracefully.
**Weaknesses:** Breaks full automation.
**Implemented in:** `02_langgraph/05_human_in_the_loop`

---

## Choosing a Pattern

| Situation | Recommended Pattern |
|-----------|---------------------|
| Simple Q&A with tools | Tool Calling |
| Open-ended research task | ReAct |
| Long multi-step project | Plan-and-Execute |
| Need high-quality output | Reflection |
| Different task types to route | Supervisor |
| Parallel independent tasks | Multi-Agent |
| High-stakes actions | Human-in-the-Loop |
